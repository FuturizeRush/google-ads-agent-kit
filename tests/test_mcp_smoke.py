import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/google-ads-mcp-setup-guide/scripts/mcp_smoke_test.py"
SPEC = importlib.util.spec_from_file_location("probe", SCRIPT)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def tool(stem, properties, required=None, prefix="sample"):
    return {"name": prefix + "_" + stem, "annotations": {"readOnlyHint": True},
            "inputSchema": {"type": "object", "properties": {key: {} for key in properties},
                            "required": required or []}}


TOOLS = [tool("list_accessible_customers", []),
         tool("get_resource_metadata", ["resource_name"]),
         tool("search", ["customer_id", "resource", "fields", "limit"])]


class FakeClient:
    def __init__(self, accounts=2, managers=False, campaigns=None, fail_first=False):
        self.ids = [f"{i:010d}" for i in range(1, accounts + 1)]
        self.managers = managers
        self.campaigns = [] if campaigns is None else campaigns
        self.fail_first = fail_first
        self.calls = []

    def request(self, method, params):
        if method == "initialize":
            return {"protocolVersion": "2025-06-18"}
        return {"tools": TOOLS}

    def send(self, *args, **kwargs):
        pass

    def call(self, selected, args):
        self.calls.append((selected["name"], args))
        if selected["name"].endswith("list_accessible_customers"):
            return self.ids
        if selected["name"].endswith("get_resource_metadata"):
            resource = args["resource_name"]
            return {"resource": resource, "selectable": ["customer.id", "customer.manager"]
                    if resource == "customer" else ["campaign.id", "campaign.name", "campaign.status"]}
        if args["resource"] == "customer":
            if self.fail_first and args["customer_id"] == self.ids[0]:
                raise probe.ProbeError("customer_not_enabled")
            return [{"customer.id": args["customer_id"], "customer.manager": self.managers}]
        return self.campaigns


class DecodeTests(unittest.TestCase):
    def test_wrapped_structured_empty_list_is_valid(self):
        value = probe.decode_tool_result({"structuredContent": {"result": []}})
        self.assertEqual(probe.require_rows(value), [])

    def test_metadata_object_is_not_flattened(self):
        data = {"resource": "campaign", "selectable": ["campaign.id"]}
        self.assertEqual(probe.decode_tool_result({"structuredContent": data}), data)

    def test_multiple_content_blocks_are_all_read(self):
        result = {"content": [{"type": "text", "text": json.dumps([{"a": 1}])},
                              {"type": "text", "text": json.dumps([{"a": 2}])}]}
        self.assertEqual(probe.decode_tool_result(result), [{"a": 1}, {"a": 2}])

    def test_unknown_dictionary_is_not_a_successful_query(self):
        with self.assertRaises(probe.ProbeError):
            probe.require_rows(probe.decode_tool_result({"structuredContent": {"unexpected": []}}))

    def test_empty_content_is_not_assumed_zero_rows(self):
        with self.assertRaises(probe.ProbeError):
            probe.decode_tool_result({"content": []})

    def test_tool_error_takes_precedence_over_structured_success(self):
        result = {"isError": True, "structuredContent": {"result": []},
                  "content": [{"type": "text", "text": "invalid_grant PRIVATE_VALUE"}]}
        with self.assertRaisesRegex(probe.ProbeError, "^oauth_reauthorization_needed$"):
            probe.decode_tool_result(result)

    def test_plain_text_success_is_not_a_row_list(self):
        with self.assertRaises(probe.ProbeError):
            probe.decode_tool_result({"content": [{"type": "text", "text": "success"}]})

    def test_bad_customer_payload_fails(self):
        for payload in ({"count": 0}, [None], ["account-name"], [12]):
            with self.subTest(payload=payload), self.assertRaises(probe.ProbeError):
                probe.require_customers(payload)


class SchemaTests(unittest.TestCase):
    def test_custom_prefix_is_discovered(self):
        self.assertEqual(probe.discover(TOOLS, "search")["name"], "sample_search")

    def test_ambiguous_tools_fail(self):
        with self.assertRaises(probe.ProbeError):
            probe.discover(TOOLS + [tool("search", [], prefix="other")], "search")

    def test_tool_without_readonly_annotation_fails(self):
        modified = dict(TOOLS[-1], annotations={})
        with self.assertRaises(probe.ProbeError):
            probe.discover([modified], "search")

    def test_metadata_parameter_variants(self):
        self.assertEqual(probe.metadata_args(TOOLS[1], "customer"), {"resource_name": "customer"})
        self.assertEqual(probe.metadata_args(tool("get_resource_metadata", ["resource"]), "campaign"), {"resource": "campaign"})

    def test_unknown_search_contract_is_rejected(self):
        with self.assertRaises(probe.ProbeError):
            probe.search_args(tool("search", ["sql"]), "sample", "campaign", ["campaign.id"], 5)

    def test_structured_and_gaql_contracts(self):
        fields = ["campaign.id"]
        self.assertEqual(probe.search_args(TOOLS[2], "sample", "campaign", fields, 5)["limit"], 5)
        legacy = tool("search", ["customer_id", "query"])
        self.assertEqual(probe.search_args(legacy, "sample", "campaign", fields, 5)["query"],
                         "SELECT campaign.id FROM campaign LIMIT 5")


class WorkflowTests(unittest.TestCase):
    def test_transport_only_makes_no_api_calls(self):
        client = FakeClient()
        report, code = probe.run_probe(client)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "TRANSPORT_ONLY")
        self.assertEqual(client.calls, [])

    def test_empty_campaigns_are_explicitly_empty(self):
        report, code = probe.run_probe(FakeClient(), live=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["accounts"][0]["campaign_query"], "PASS_EMPTY")
        self.assertEqual(report["accounts"][0]["campaign_rows"], 0)
        self.assertEqual(report["host_integration"], "NOT_TESTED")

    def test_disabled_first_account_does_not_hide_second(self):
        report, code = probe.run_probe(FakeClient(fail_first=True), live=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["accounts"][0]["error"], "customer_not_enabled")
        self.assertEqual(report["accounts"][1]["campaign_query"], "PASS_EMPTY")

    def test_managers_are_not_client_success(self):
        client = FakeClient(managers=True)
        report, code = probe.run_probe(client, live=True)
        self.assertEqual(code, 2)
        self.assertEqual(report["successful_campaign_queries"], 0)
        self.assertFalse(any(args.get("resource") == "campaign" for _, args in client.calls))

    def test_bounds_and_no_account_identity_in_report(self):
        client = FakeClient(accounts=7)
        report, code = probe.run_probe(client, live=True, max_accounts=3)
        self.assertEqual(code, 0)
        self.assertEqual(len(report["accounts"]), 3)
        self.assertEqual(report["accounts_not_probed"], 4)
        output = json.dumps(report)
        for cid in client.ids:
            self.assertNotIn(cid, output)

    def test_campaign_data_never_enters_report(self):
        client = FakeClient(campaigns=[{"campaign.id": "sample-id", "campaign.name": "PRIVATE_CAMPAIGN", "campaign.status": "PAUSED"}])
        report, code = probe.run_probe(client, live=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["accounts"][0]["campaign_rows"], 1)
        self.assertNotIn("PRIVATE_CAMPAIGN", json.dumps(report))

    def test_wrong_shape_and_excess_rows_do_not_pass(self):
        for rows in ({"unexpected": []}, [{}], [{}] * 6):
            client = FakeClient(campaigns=rows)
            report, code = probe.run_probe(client, live=True)
            self.assertEqual(code, 2)
            self.assertEqual(report["successful_campaign_queries"], 0)

    def test_missing_metadata_field_stops_before_search(self):
        client = FakeClient()
        with patch.object(probe, "fields_from_metadata", side_effect=probe.ProbeError("required_fields_not_selectable")):
            with self.assertRaises(probe.ProbeError):
                probe.run_probe(client, live=True)
        self.assertFalse(any(name.endswith("_search") for name, _ in client.calls))


class TransportTests(unittest.TestCase):
    def test_buffered_notifications_do_not_lose_response(self):
        server = "import sys,json; q=json.loads(input()); print(json.dumps({'jsonrpc':'2.0','method':'notifications/test'})); print(json.dumps({'jsonrpc':'2.0','id':q['id'],'result':{'ok':True}})); sys.stdout.flush(); input()"
        with probe.MCPClient([sys.executable, "-u", "-c", server], timeout=2) as client:
            self.assertEqual(client.request("sample"), {"ok": True})

    def test_timeout_is_bounded_and_process_is_closed(self):
        with probe.MCPClient([sys.executable, "-u", "-c", "import time; time.sleep(10)"], timeout=0.1) as client:
            with self.assertRaisesRegex(probe.ProbeError, "^timeout$"):
                client.request("sample")
        self.assertIsNotNone(client.proc.poll())

    def test_raw_protocol_noise_is_never_echoed(self):
        server = "print('PRIVATE_PROTOCOL_NOISE', flush=True)"
        with probe.MCPClient([sys.executable, "-u", "-c", server], timeout=2) as client:
            with self.assertRaisesRegex(probe.ProbeError, "^(invalid_protocol_output|server_closed_stdin)$"):
                client.request("sample")

    def test_http_proxy_settings_prevent_launch(self):
        with patch.dict(os.environ, {"GOOGLE_ADS_MCP_OAUTH_CLIENT_ID": "example", "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET": "example"}):
            with self.assertRaisesRegex(probe.ProbeError, "^http_proxy_environment_present$"):
                with probe.MCPClient(["does-not-exist"]):
                    pass


if __name__ == "__main__":
    unittest.main()
