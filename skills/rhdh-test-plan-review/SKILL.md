---
name: rhdh-test-plan-review
description: |
  Reviews an RHDH test plan Jira ticket and suggests platform/integration version updates based on support lifecycle pages and RHDH release milestones. Use when given an RHDH test plan Jira ticket ID to check which platform/integration versions to add or remove. Use when asked to "update test plan", "review test plan", "check platform versions in test plan", "review RHDH test plan", "what platforms should we test for RHDH X", or "update supported versions in test plan".
---

<essential_principles>

<principle name="no_changes_without_approval">
Never modify Jira tickets without explicit user approval. Collect all decisions first, summarize them, then ask whether to apply — direct update [d], comment [c], or discard [n].
</principle>

<principle name="version_tracking_rules">
Different platforms accumulate versions differently:
- **OCP**: accumulate all active versions
- **AKS, EKS, GKE, Quay**: single latest version only — replace, never accumulate
- **ARO, OSD, ROSA**: single version each, evaluated independently — replace if a newer version is GA before code_freeze
- **RHBK**: track major versions only (e.g., `26` not `26.0`); accumulate all active majors
- **PostgreSQL**: RHDH support policy is the baseline; Backstage-only versions require a Jira Feature ticket warning
</principle>

<principle name="milestone_cutoffs">
Add/remove decisions are based on `code_freeze` and `ga_date` from the RHDH schedule sheet — not today's date.
- **Add**: version GA date ≤ `code_freeze`
- **Remove**: version EOL date ≤ `ga_date`
</principle>

<principle name="adf_preservation">
Jira descriptions are ADF (nested JSON). When updating, modify only version strings and date cells inside existing table cells — never convert to plain text and back. Preserve all other ADF structure exactly.
</principle>

<principle name="token_safety">
Never read `.jira-token` into context. Always use shell substitution: `"$(cat "$TOKEN_FILE")"`.
</principle>

</essential_principles>

<intake>

## RHDH Test Plan Review

Provide a Jira ticket ID or URL (e.g., `RHIDP-8994`) to begin.

**Wait for response before proceeding.**

</intake>

<routing>

| Input | Workflow |
|-------|----------|
| Jira ticket ID or URL | Read `workflows/review-test-plan.md` and follow it |

</routing>

<reference_index>

| Reference | Purpose | Path |
|-----------|---------|------|
| sources | Lifecycle URLs and extraction guidance per platform/integration | `references/sources.md` |
| google-sheets-setup | One-time gcloud auth setup for schedule sheet access | `references/google-sheets-setup.md` |
| rhdh-jira auth | Jira REST API token setup and curl patterns | `../rhdh-jira/references/auth.md` |

</reference_index>

<success_criteria>

- [ ] RHDH version extracted from ticket
- [ ] Milestone dates fetched from schedule sheet
- [ ] All platform and integration versions checked against lifecycle sources
- [ ] Overview diff presented (key dates, platforms, integrations)
- [ ] Each proposed change reviewed interactively (a/k/e)
- [ ] User chose how to apply: [d] direct update, [c] comment, [n] discard
- [ ] If [d]: Jira description updated via REST API; child tasks offered one at a time
- [ ] If [c]: comment posted to ticket
- [ ] If [n]: confirmed no changes were made

</success_criteria>
