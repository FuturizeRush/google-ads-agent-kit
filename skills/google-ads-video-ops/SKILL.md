---
name: google-ads-video-ops
description: Review Google Ads Video campaign delivery, budgets, target CPV, audiences, and frequency; apply explicitly authorized changes and verify persisted settings. Use for zero-view diagnosis or Video campaign optimization, not MCP installation or other campaign types.
---

# Google Ads Video operations

Separate three questions: is the campaign configured correctly, is it delivering, and is it reaching useful prospects? Evidence for one does not answer the others.

## Select the work

- Diagnose missing views or review current configuration: read [delivery diagnostics](references/delivery-diagnostics.zh-TW.md). Keep the account read-only.
- Recommend bids, audiences, formats, or frequency: also read [decision criteria](references/decision-criteria.zh-TW.md). Preserve the user's commercial constraints; do not turn a previous campaign's values into defaults.
- Apply an agreed change: read [safe changes](references/safe-changes.zh-TW.md) before writing. Confirm the exact target and authorized changes, including budget type, currency, amount, dates, and any change that broadens delivery. A request to review is not permission to edit.

These references describe Video campaigns. Check the actual campaign subtype and current controls; do not transfer these bidding or frequency rules to Demand Gen, Search, or Performance Max.

## Establish scope and capabilities

Resolve the intended enabled client account, campaign, and relevant ad group/ad before acting. Verify account currency and time zone. Do not pick the first accessible account or infer currency from `$`.

Prefer an available Google Ads connector. Inspect its current tools and input schemas, then resource metadata before querying. Tool annotations are hints, not proof of authorization or capability. When only read tools are exposed, do not invent a mutation call. Use the authenticated Ads UI for authorized edits if available; otherwise hand off the exact changes and report that they are not applied. This skill does not require a specific MCP package or grant permission to install one.

Read only fields needed for the question. Keep account identifiers, raw responses, screenshots, change records, and destination tracking values in the user's private workspace, outside any public repository. Never request or print OAuth secrets. Public examples must be synthetic, not lightly renamed account exports.

## Preserve the evidence boundary

- Read current values immediately before writing. If user edits changed the assumptions, reconcile them; do not overwrite with an old snapshot.
- Tie amounts to currency, budget period, and the active strategy field. Use exact decimal arithmetic for micros.
- Check shared-object usage before changing an audience, budget, or asset. Permission for one campaign does not cover its other consumers.
- Verify saved state by reopening the UI or making an independent read query. Stop on conflicting state, ambiguous save, authentication challenge, or a required change outside authorization; do not repeatedly submit or escalate spend.
- Report applied, unchanged, and pending/unverified items separately. `ENABLED`, `ELIGIBLE`, and a saved form do not prove impressions, views, approval, or purchases.

## Handoff

Lead with the finding or completed change. Include the relevant budget/bid/date result, any review or access blocker, and what evidence would settle the remaining question. A compact before/after table is useful for several edited fields. Avoid narrating every click, promising delivery, or claiming purchase attribution from UTM parameters alone. Create monitoring only when the user requests it.
