# Public content and credentials

This repository contains teaching material, community skills, synthetic tests, and local verification helpers. No Google credentials or real Ads account / campaign data are required to install the skills or run their offline tests.

Do not commit `.env`, OAuth client downloads, ADC JSON, service account keys, raw MCP logs, account exports, screenshots containing account details, or private conversation transcripts. Keep credentials outside this checkout. `.gitignore` is a convenience, not a secret-removal mechanism.

The live probe uses existing ADC through the official server and performs read-only queries. The underlying OAuth consent can grant broader authority than these queries. Read the consent screen. Output omits identities and raw errors, but counts can still be confidential; do not post a live report without reviewing it.

## Release checks

Before each public push, check the explicit file allowlist, working-tree content and paths, staged blob content and modes, reachable Git history and commit metadata, known private values, and a separate Gitleaks scan. The public helper can compare to a local private file without printing its values:

```bash
python3 scripts/check_public_tree.py --history --private-file /ABSOLUTE/PATH/TO/PRIVATE/credentials.json
gitleaks dir . --redact --no-banner
gitleaks git . --redact --no-banner --log-opts="--all"
```

Replace the example private path locally; never add that file to Git. Private-file comparison is not performed in GitHub Actions because no personal credentials are supplied to CI. CI runs synthetic offline tests, the public-tree policy, and Gitleaks against repository files and reachable history.

For campaign context that is not a credential, an outside-repository JSON file may contain a `sensitive_values` array of strings (at least six characters each). Include distinctive campaign/audience names, product and video URLs, affiliate values, and other private identifiers. The helper also reads recognized credential and account identifier fields. Never commit the comparison list itself or use real values in test fixtures.

Keep account-specific baselines and decisions outside this checkout. Public skills should describe reusable decisions and verification methods, not copy a real campaign's dates, bids, demographics, or creative choices as defaults. Review links, examples, screenshots, generated reports, and test artifacts manually: removing a name alone does not make a case anonymous. A clean working tree does not prove a clean staged snapshot or clean history.

The checks are evidence about the scanned files and revisions, not a promise that a detector can find every possible secret. New files require an intentional update to `.public-files`, another content review, and another history scan.

## Reporting a problem

For a documentation or script defect, open a minimal issue with synthetic input. Do not paste a token, credential file, account ID, or real campaign data into an issue. If credentials were exposed elsewhere, follow Google's revocation / rotation guidance before further troubleshooting; deleting a working-tree file alone does not revoke access.
