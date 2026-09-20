---
name: google-ads-mcp-setup-guide
description: Install and verify the official Google Ads MCP server with gcloud ADC, connect an AI client, and diagnose onboarding failures. Use for Google Ads MCP setup or read-only connectivity tests, not campaign optimization or ad changes.
---

# Google Ads MCP setup guide

Help the user reach a verified, read-only Google Ads query from their chosen AI client. Preserve existing accounts, credentials, and unrelated client configuration. This is a community skill, not a Google product.

## Choose the relevant path

- New setup: read [the installation tutorial](references/tutorial.zh-TW.md). It covers gcloud CLI, official Google skills, OAuth, MCP installation, and Codex registration. macOS is the tested path; other platforms link to official installers.
- A specific error: read [troubleshooting](references/troubleshooting.zh-TW.md) and check the failing layer only.
- Time-sensitive behavior or conflicting guidance: consult [sources and version notes](references/sources.md). Treat live official policy, the installed package, and the server's `tools/list` as evidence; a cached skill is not proof of current behavior.

## Establish what is actually available

Distinguish these outcomes: skill files installed; server installed; MCP handshake works; ADC authenticates; an account query works; a campaign query returns a valid list; the chosen AI host can invoke that server. Evidence for one does not prove the next.

Check executables and package metadata before installing anything. Validate gcloud login syntax with `gcloud help auth application-default login` before proposing the command. For an explanation-only request, explain; do not install or register tools merely because this skill describes how.

The scope here is local stdio with the official `google-ads-mcp` package. Do not open a network listener, configure an OAuth proxy, or deploy a server as a side effect of setup.

## Credentials and current policy

As checked on 2026-09-20, Google moved Google Ads API access levels to Cloud projects on 2026-09-09. Do not require a new Developer Token for this workflow. Recheck the policy source if it changes. Enabling the API grants Test access; querying production accounts also needs a suitable project access level.

For the tested package, local OAuth uses ADC. Having `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, or `GOOGLE_ADS_REFRESH_TOKEN` in `.env` does not prove ADC exists, and the server does not automatically load arbitrary `.env` files. Prefer the existing valid ADC. If login is needed, the account owner completes the browser consent flow. Do not ask them to paste tokens, authorization codes, or credential JSON into chat.

An OAuth grant can be broader than the server's read-only tools. Explain the requested scopes; do not describe the credentials themselves as read-only. `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is a routing setting for manager access, not a password and not mandatory for every direct-access account.

## Verify using the real tool schema

Prefer the host's existing Google Ads MCP tools when available. Otherwise run the bundled protocol probe with the official executable. It launches a local subprocess and does not register it with any host:

```bash
python3 scripts/mcp_smoke_test.py
python3 scripts/mcp_smoke_test.py --live
```

These paths are relative to this skill directory; resolve the actual installed skill directory first. Default mode only performs MCP initialization and tool discovery. `--live` makes bounded read-only API calls and uses existing credentials. It reports counts and generic error categories, never account IDs, campaign names, tokens, or raw server logs. Counts may still be business-sensitive; keep live output local.

Use `--customer-id` only for a user-selected account; otherwise the probe tries at most five directly accessible accounts. It skips managers for campaign queries. If only a manager is accessible, identify the intended child account with the user or an authorized hierarchy query; do not treat a manager's empty campaign list as the client's result.

Always inspect `tools/list`. The tested defaults are `customers_list_accessible_customers`, `metadata_get_resource_metadata(resource_name)`, and `search_search(customer_id, fields, resource, ...)`. Namespaces can be customized. Read metadata for each resource before constructing its query. Do not blindly reuse a `query` argument from an older guide.

The tested toolset provides reads, not campaign mutations. Successful authentication does not add missing write tools. For an authorized campaign change, use an available supported write interface or the Ads UI; do not reinstall a working server or fabricate a mutation endpoint. Campaign strategy belongs in a campaign review workflow, not this setup flow.

Treat `isError`, protocol errors, unexpected output shapes, and timeouts as failures. A valid empty campaign list is `PASS_EMPTY`, not proof that campaigns exist. Report row counts and selection limits locally. Check host registration separately; a subprocess test does not prove the current chat has the tool.

## Finish in plain language

State what works, the exact failing layer if any, and the next concrete step. Avoid reporting “all connected” when only installation or authentication is verified. Keep credentials, account identities, campaign data, and local transcripts out of any public artifact.
