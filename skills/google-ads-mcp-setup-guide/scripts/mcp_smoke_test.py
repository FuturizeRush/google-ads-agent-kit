#!/usr/bin/env python3
"""Bounded Google Ads MCP probe. Standard library only; no raw account output."""

import argparse
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time


class ProbeError(Exception):
    """A fixed, non-sensitive error category that is safe to display."""


def classify_error(message):
    text = message.lower()
    rules = (
        ("default credentials", "adc_missing_or_invalid"),
        ("invalid_grant", "oauth_reauthorization_needed"),
        ("invalid_client", "oauth_client_invalid"),
        ("cloud_project_not_approved", "project_access_level"),
        ("not yet enabled", "customer_not_enabled"),
        ("deactivated", "customer_not_enabled"),
        ("two_step_verification", "account_verification_required"),
        ("insufficient authentication scopes", "oauth_scope_missing"),
        ("access_token_scope_insufficient", "oauth_scope_missing"),
        ("permission", "permission_denied"),
        ("unauthenticated", "authentication_failed"),
    )
    return next((category for needle, category in rules if needle in text), "api_or_tool_error")


def unwrap(value):
    for _ in range(4):
        if isinstance(value, dict) and set(value) == {"result"}:
            value = value["result"]
        else:
            return value
    raise ProbeError("unexpected_output_shape")


def decode_tool_result(result):
    if not isinstance(result, dict):
        raise ProbeError("unexpected_output_shape")
    if result.get("isError"):
        message = " ".join(
            block.get("text", "") for block in result.get("content", [])
            if isinstance(block, dict) and isinstance(block.get("text", ""), str)
        )
        raise ProbeError(classify_error(message))
    if result.get("structuredContent") is not None:
        return unwrap(result["structuredContent"])
    blocks = result.get("content")
    if not isinstance(blocks, list) or not blocks:
        raise ProbeError("unexpected_output_shape")
    values = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "text":
            raise ProbeError("unexpected_output_shape")
        try:
            values.append(json.loads(block["text"]))
        except (KeyError, TypeError, ValueError):
            raise ProbeError("unexpected_output_shape") from None
    if len(values) == 1:
        return unwrap(values[0])
    if all(isinstance(item, list) for item in values):
        return [row for items in values for row in items]
    return values


def require_rows(payload):
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ProbeError("unexpected_row_shape")
    return payload


def require_customers(payload):
    if not isinstance(payload, list):
        raise ProbeError("unexpected_customer_shape")
    if not all(isinstance(cid, str) and re.fullmatch(r"\d{10}", cid) for cid in payload):
        raise ProbeError("unexpected_customer_shape")
    return list(dict.fromkeys(payload))


def discover(tools, stem):
    if not isinstance(tools, list):
        raise ProbeError("unexpected_tool_list")
    matches = [tool for tool in tools if isinstance(tool, dict)
               and (tool.get("name") == stem or tool.get("name", "").endswith("_" + stem))]
    if len(matches) != 1:
        raise ProbeError("missing_or_ambiguous_tool")
    tool = matches[0]
    if (tool.get("annotations") or {}).get("readOnlyHint") is not True:
        raise ProbeError("read_only_annotation_missing")
    schema = tool.get("inputSchema")
    if not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict):
        raise ProbeError("unsupported_tool_schema")
    return tool


def metadata_args(tool, resource):
    properties = tool["inputSchema"]["properties"]
    for name in ("resource_name", "resource"):
        if name in properties:
            return {name: resource}
    raise ProbeError("unsupported_metadata_schema")


def search_args(tool, customer_id, resource, fields, limit):
    properties = tool["inputSchema"]["properties"]
    if {"customer_id", "resource", "fields", "limit"} <= properties.keys():
        return {"customer_id": customer_id, "resource": resource, "fields": fields, "limit": limit}
    if {"customer_id", "query"} <= properties.keys():
        return {"customer_id": customer_id,
                "query": f"SELECT {', '.join(fields)} FROM {resource} LIMIT {limit}"}
    raise ProbeError("unsupported_search_schema")


class MCPClient:
    def __init__(self, command, timeout=25):
        self.command = command
        self.timeout = timeout
        self.inbox = queue.Queue()
        self.sequence = 0

    def __enter__(self):
        # The official server selects HTTP if these are set; do not open a listener.
        if os.environ.get("GOOGLE_ADS_MCP_OAUTH_CLIENT_ID") and os.environ.get("GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET"):
            raise ProbeError("http_proxy_environment_present")
        try:
            self.proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        except OSError:
            raise ProbeError("server_start_failed") from None
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        return self

    def _read(self):
        try:
            for line in self.proc.stdout:
                try:
                    obj = json.loads(line)
                    self.inbox.put(obj if isinstance(obj, dict) else ProbeError("invalid_protocol_output"))
                except ValueError:
                    self.inbox.put(ProbeError("invalid_protocol_output"))
        except (OSError, UnicodeError):
            self.inbox.put(ProbeError("invalid_protocol_output"))
        finally:
            self.inbox.put(ProbeError("server_closed_stdout"))

    def send(self, method, params=None, notification=False):
        self.sequence += 1
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if not notification:
            message["id"] = self.sequence
        try:
            self.proc.stdin.write(json.dumps(message) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError):
            raise ProbeError("server_closed_stdin") from None
        return self.sequence

    def request(self, method, params=None):
        ident = self.send(method, params)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                message = self.inbox.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty:
                break
            if isinstance(message, ProbeError):
                raise message
            if message.get("id") != ident:
                continue
            if "error" in message:
                raise ProbeError("mcp_protocol_error")
            if "result" not in message:
                raise ProbeError("invalid_protocol_output")
            return message["result"]
        raise ProbeError("timeout")

    def call(self, tool, arguments):
        properties = tool["inputSchema"]["properties"]
        required = set(tool["inputSchema"].get("required", []))
        if not required <= arguments.keys() or not arguments.keys() <= properties.keys():
            raise ProbeError("unsupported_tool_schema")
        return decode_tool_result(self.request("tools/call", {"name": tool["name"], "arguments": arguments}))

    def __exit__(self, *exc):
        self.proc.stdin.close()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3)
        self.reader.join(timeout=1)
        self.proc.stdout.close()


def fields_from_metadata(client, tool, resource, wanted):
    data = client.call(tool, metadata_args(tool, resource))
    if not isinstance(data, dict) or data.get("resource") != resource:
        raise ProbeError("unexpected_metadata_shape")
    selectable = data.get("selectable")
    if not isinstance(selectable, list) or not set(wanted) <= set(selectable):
        raise ProbeError("required_fields_not_selectable")
    return wanted


def run_probe(client, live=False, customer_id=None, max_accounts=5):
    init = client.request("initialize", {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "google-ads-agent-kit", "version": "1.0"}})
    if not isinstance(init, dict) or init.get("protocolVersion") not in {
        "2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"
    }:
        raise ProbeError("unsupported_protocol_version")
    client.send("notifications/initialized", notification=True)
    tools = []
    cursor = None
    for _ in range(10):
        page = client.request("tools/list", {"cursor": cursor} if cursor else {})
        if not isinstance(page, dict) or not isinstance(page.get("tools"), list):
            raise ProbeError("unexpected_tool_list")
        tools.extend(page["tools"])
        cursor = page.get("nextCursor")
        if not cursor:
            break
    else:
        raise ProbeError("tool_pagination_limit")
    selected = {stem: discover(tools, stem) for stem in
                ("list_accessible_customers", "get_resource_metadata", "search")}
    report = {"transport": "PASS", "tool_discovery": "PASS", "live_requested": live,
              "host_integration": "NOT_TESTED"}
    if not live:
        report["status"] = "TRANSPORT_ONLY"
        return report, 0

    customers = require_customers(client.call(selected["list_accessible_customers"], {}))
    report["accessible_account_count"] = len(customers)
    candidates = [customer_id] if customer_id else customers[:max_accounts]
    report["accounts_not_probed"] = None if customer_id else max(0, len(customers) - len(candidates))
    metadata = selected["get_resource_metadata"]
    search = selected["search"]
    customer_fields = fields_from_metadata(client, metadata, "customer", ["customer.id", "customer.manager"])
    campaign_fields = fields_from_metadata(client, metadata, "campaign", ["campaign.id", "campaign.name", "campaign.status"])
    report["metadata"] = "PASS"
    report["accounts"] = []
    successes = 0
    for index, cid in enumerate(candidates, 1):
        item = {"label": f"account_{index}"}
        report["accounts"].append(item)
        try:
            rows = require_rows(client.call(search, search_args(search, cid, "customer", customer_fields, 1)))
            if len(rows) != 1 or not isinstance(rows[0].get("customer.manager"), bool):
                raise ProbeError("unexpected_customer_rows")
            if str(rows[0].get("customer.id")) != cid:
                raise ProbeError("customer_identity_mismatch")
            item["customer_query"] = "PASS"
            if rows[0]["customer.manager"]:
                item["campaign_query"] = "SKIPPED_MANAGER_SELECT_CHILD"
                continue
            campaigns = require_rows(client.call(search, search_args(search, cid, "campaign", campaign_fields, 5)))
            if len(campaigns) > 5 or any(not set(campaign_fields) <= row.keys() for row in campaigns):
                raise ProbeError("unexpected_campaign_rows")
            item.update(campaign_query="PASS_WITH_ROWS" if campaigns else "PASS_EMPTY",
                        campaign_rows=len(campaigns), limit=5)
            successes += 1
        except ProbeError as exc:
            item["error"] = str(exc)
            if str(exc) in {"timeout", "invalid_protocol_output", "server_closed_stdout", "server_closed_stdin"}:
                raise
    report["successful_campaign_queries"] = successes
    report["status"] = "LIVE_QUERY_VERIFIED" if successes else "NO_CLIENT_QUERY_VERIFIED"
    return report, 0 if successes else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="google-ads-mcp", help="Official server executable or path")
    parser.add_argument("--live", action="store_true", help="Run bounded read-only Google Ads API calls")
    parser.add_argument("--customer-id", help="Optional selected client ID; do not publish this value")
    parser.add_argument("--max-accounts", type=int, default=5, choices=range(1, 6))
    parser.add_argument("--timeout", type=int, default=25, choices=range(1, 61))
    args = parser.parse_args()
    if args.customer_id and (not args.live or not re.fullmatch(r"\d{10}", args.customer_id)):
        parser.error("--customer-id requires --live and exactly ten digits")
    executable = shutil.which(args.server)
    if executable is None:
        print(json.dumps({"status": "FAIL", "error": "server_executable_not_found"}))
        return 2
    try:
        with MCPClient([str(Path(executable).resolve())], args.timeout) as client:
            report, code = run_probe(client, args.live, args.customer_id, args.max_accounts)
    except ProbeError as exc:
        report, code = {"status": "FAIL", "error": str(exc)}, 2
    except Exception:
        # Exceptions can embed credentials or query results; keep details local.
        report, code = {"status": "FAIL", "error": "unexpected_local_error"}, 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
