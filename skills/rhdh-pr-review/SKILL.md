---
name: rhdh-pr-review
description: Test PR changes on a live RHDH cluster. Fetches CI-built images from PR comments, checks cluster status (deploying if needed), swaps images into the running deployment, and generates a targeted review checklist from the diff. Use when asked to review an rhdh-operator PR, test PR changes on a cluster, swap CI images, or deploy PR images for testing. Also use when user mentions "operator PR", "review PR", or "test this PR on my cluster". Currently supports rhdh-operator PRs.
---

<essential_principles>

<principle name="ensure_cluster">
Always verify the user has a running RHDH cluster with `oc` access before attempting image swaps.
Check `oc whoami` and `oc get deployment -A | grep rhdh-operator` first.
If no cluster at all (`oc whoami` fails), **provision one via rhdh-test-instance PR workflow** — comment `/test deploy operator 1.9 4h` on a PR in `redhat-developer/rhdh-test-instance` using `gh pr comment`. No local clone needed.
If cluster exists but no RHDH, deploy using rhdh-test-instance locally (`make install-operator && make deploy-operator`).
Don't just tell the user to set things up — do it.
</principle>

<principle name="use_pr_comment_images">
Extract image URLs from PR comments posted by CI — never construct image URLs manually.
The tag format includes PR number + commit SHA, which only CI knows.
See `references/operator-pr-images.md` for extraction commands.
</principle>

<principle name="patch_not_redeploy">
Swap images on a running deployment rather than redeploying from scratch.
For non-OLM installs, use `oc set image`. For OLM-managed installs, patch the CSV — never patch the Deployment directly as OLM will overwrite it. This is faster and preserves existing state (Backstage CRs, config, Keycloak).
</principle>

</essential_principles>

<intake>

## What would you like to do?

### PR Review Tasks

*For testing PR changes on a live RHDH cluster*

1. **Review rhdh-operator PR** — Swap CI images into cluster and get review checklist

**Wait for response before proceeding.**

</intake>

<routing>

### PR Review Routes

| Response | Workflow |
|----------|----------|
| 1, "operator", "rhdh-operator", a PR number, "review" | Route to `workflows/review-operator-pr.md` |

**To route:** Read `workflows/review-operator-pr.md` and follow its process.

</routing>

<reference_index>

| Reference | Purpose | Path |
|-----------|---------|------|
| operator-pr-images | CI image naming, registry, extraction, expiry | `references/operator-pr-images.md` |
| github-reference | gh CLI patterns, PR queries | `../../rhdh/references/github-reference.md` |
| rhdh-repos | RHDH ecosystem repository map | `../../rhdh/references/rhdh-repos.md` |

</reference_index>

<skills_index>

| Skill | Purpose | Path |
|-------|---------|------|
| rhdh | Orchestrator, environment status, activity tracking | `../../rhdh/SKILL.md` |

</skills_index>

<success_criteria>

PR review session is complete when:

- [ ] PR images identified from CI comment and validated in registry
- [ ] Cluster has RHDH operator running with the PR image
- [ ] Review checklist generated from diff analysis
- [ ] Rollback instructions documented
- [ ] Activity logged via `$RHDH log add`

</success_criteria>
