# Workflow: Review rhdh-operator PR on Live Cluster

Fetch a PR's CI-built operator image, swap it into a running RHDH cluster, and generate a targeted review checklist from the diff.

<required_reading>

Read these reference files before starting:

1. `../references/operator-pr-images.md` — Image naming, extraction, validation
2. `../../rhdh/references/github-reference.md` — gh CLI patterns

</required_reading>

<prerequisites>

| Requirement | Details |
|-------------|---------|
| **Input** | PR number for rhdh-operator (or full PR URL) |
| **Access** | Read access to `redhat-developer/rhdh-operator` |
| **Tools** | `gh` CLI authenticated, `oc` CLI available |
| **Cluster** | Running OpenShift cluster (will offer to deploy if no RHDH instance) |

</prerequisites>

<process>

## Phase 1: Fetch PR Context

```bash
REPO="redhat-developer/rhdh-operator"
PR_NUMBER=<number>

gh pr view $PR_NUMBER --repo $REPO \
  --json number,title,state,author,body,files,createdAt,headRefOid
```

Validate:
- PR state is `OPEN` (warn if merged or closed — images may still work but PR is not active)
- PR belongs to `redhat-developer/rhdh-operator`

Fetch the diff for later checklist generation:

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

Save the changed file list for Phase 5:

```bash
gh pr view $PR_NUMBER --repo $REPO --json files --jq '.files[].path'
```

---

## Phase 2: Extract CI-Built Images

Find the CI comment with image URLs:

```bash
gh pr view $PR_NUMBER --repo $REPO --json comments \
  --jq '.comments[] | select(.body | test("quay.io/rhdh-community/operator:")) | .body' \
  | tail -1
```

Parse out three image URLs:
- `quay.io/rhdh-community/operator:<tag>`
- `quay.io/rhdh-community/operator-bundle:<tag>`
- `quay.io/rhdh-community/operator-catalog:<tag>`

**If no CI comment found**, check workflow status:

```bash
BRANCH=$(gh pr view $PR_NUMBER --repo $REPO --json headRefName --jq '.headRefName')
gh run list --repo $REPO --branch $BRANCH --workflow pr-container-build.yaml --limit 1 \
  --json status,conclusion
```

- If `in_progress` — tell user to wait and check back
- If `failure` — report build failure, link to workflow run
- If no runs — explain CI may not have triggered (draft PR, docs-only change, external contributor)

**Validate the operator image exists:**

```bash
skopeo inspect docker://quay.io/rhdh-community/operator:<tag> --raw 2>/dev/null
```

If validation fails, warn that images may have expired (14-day TTL).

---

## Phase 3: Ensure a Running RHDH Cluster

### 3.1 Verify cluster access

```bash
oc whoami 2>&1
oc cluster-info 2>/dev/null | head -2
```

### 3.2 Check for running RHDH operator

```bash
oc get deployment -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name \
  --no-headers 2>/dev/null | grep -i rhdh-operator
```

### 3.3 Check for Backstage CR

```bash
oc get backstage -A 2>/dev/null
```

### 3.4 Decision tree

| Cluster state | Action |
|---------------|--------|
| Operator running + Backstage CR exists | Skip to Phase 4 |
| Cluster accessible but no RHDH operator | Deploy RHDH on existing cluster (see 3.5b) |
| No cluster access (`oc whoami` fails) | Provision a cluster via rhdh-test-instance PR (see 3.5a) |

### 3.5 Provision or deploy RHDH

Read `../references/cluster-provisioning.md` and follow the appropriate section:

- **No cluster at all** (`oc whoami` fails) → follow `<provision_via_pr>` to provision a cluster via rhdh-test-instance PR workflow
- **Cluster accessible but no RHDH** → follow `<deploy_on_existing_cluster>` to deploy RHDH locally

Once the operator and Backstage CR are healthy, proceed to Phase 4.

---

## Phase 4: Swap Operator Image

### 4.1 Detect install method

```bash
oc get subscription -A 2>/dev/null | grep -i rhdh
```

- If Subscription found → **OLM-managed** (use 4.4a)
- If no Subscription → **direct deployment** (use 4.4b)

### 4.2 Identify operator deployment and namespace

```bash
OPERATOR_NS=$(oc get deployment -A --no-headers \
  -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name \
  | grep rhdh-operator | awk '{print $1}')

OPERATOR_DEPLOY=$(oc get deployment -n $OPERATOR_NS --no-headers \
  -o custom-columns=NAME:.metadata.name | grep rhdh-operator)
```

### 4.3 Record current image (for rollback)

```bash
CURRENT_IMAGE=$(oc get deployment $OPERATOR_DEPLOY -n $OPERATOR_NS \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="manager")].image}')
echo "Current operator image: $CURRENT_IMAGE"
```

### 4.4a Swap image — OLM-managed install

**IMPORTANT:** Do NOT use `oc set image` or patch the Deployment directly — OLM owns the Deployment and will overwrite any direct changes. Patch the CSV instead.

```bash
PR_IMAGE="quay.io/rhdh-community/operator:<tag>"

# Find the CSV name
CSV_NAME=$(oc get csv -n $OPERATOR_NS --no-headers \
  -o custom-columns=NAME:.metadata.name | grep rhdh)

# Record current CSV image for rollback
CSV_CURRENT_IMAGE=$(oc get csv $CSV_NAME -n $OPERATOR_NS \
  -o jsonpath='{.spec.install.spec.deployments[0].spec.template.spec.containers[0].image}')
echo "Current CSV image: $CSV_CURRENT_IMAGE"

# Patch the CSV to use the PR image
oc patch csv $CSV_NAME -n $OPERATOR_NS --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/image\", \"value\": \"$PR_IMAGE\"}]"
```

OLM will detect the CSV change and roll out a new operator pod automatically.

### 4.4b Swap image — direct deployment (non-OLM)

```bash
PR_IMAGE="quay.io/rhdh-community/operator:<tag>"

oc set image deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS \
  manager=$PR_IMAGE
```

### 4.5 Wait for rollout

```bash
oc rollout status deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --timeout=120s
```

### 4.6 Verify the swap

```bash
# Confirm new image is running
oc get deployment $OPERATOR_DEPLOY -n $OPERATOR_NS \
  -o jsonpath='{.spec.template.spec.containers[0].image}'

# Check pod is healthy
oc get pods -n $OPERATOR_NS -l control-plane=controller-manager

# Check operator logs for errors
oc logs deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --tail=20

# Check Backstage CR health
RHDH_NS=$(oc get backstage -A --no-headers 2>/dev/null | head -1 | awk '{print $1}')
if [ -n "$RHDH_NS" ]; then
  oc get backstage -n $RHDH_NS
  oc get pods -n $RHDH_NS
fi
```

### 4.7 Document rollback

Present rollback commands to the user:

**OLM-managed — restore CSV image:**

```bash
oc patch csv $CSV_NAME -n $OPERATOR_NS --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/image\", \"value\": \"$CSV_CURRENT_IMAGE\"}]"
```

**Non-OLM — revert deployment image:**

```bash
oc set image deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS \
  manager=$CURRENT_IMAGE
```

---

## Phase 5: Generate Review Checklist

Analyze the diff from Phase 1 and categorize changed files:

| File pattern | Category | Review focus |
|-------------|----------|--------------|
| `api/`, `*_types.go` | CRD/API | New fields, deprecations, backward compatibility |
| `internal/controller/`, `pkg/model/` | Controller/Reconciler | Reconciliation behavior, status updates, edge cases |
| `config/profile/`, `default-config/` | Default config | Verify defaults applied, check for regressions |
| `*_test.go`, `integration_tests/` | Tests | Run the new/modified tests |
| `.github/`, `Makefile`, `Dockerfile` | Build/CI | Verify builds still work |
| `docs/`, `*.md` | Documentation | Review for accuracy |
| `go.mod`, `go.sum` | Dependencies | Check for major version bumps |

### Generate the checklist

For each category with changes, generate specific verification items.

**Always include these baseline checks:**

```markdown
### Baseline Checks
- [ ] Operator pod started successfully with PR image (no crash loops)
- [ ] Operator logs show no errors (`oc logs deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --tail=50`)
- [ ] Existing Backstage CR reconciled without errors
- [ ] RHDH pods are running and healthy
```

**CRD/API changes — add:**

```markdown
### CRD/API Verification
- [ ] Apply a Backstage CR with the new/changed field(s) set
- [ ] Apply a Backstage CR without the new field(s) — verify backward compatibility
- [ ] Verify existing CRs still reconcile correctly after CRD update
- [ ] Check `oc explain backstage.spec.<new-field>` shows correct schema
```

**Controller/Reconciler changes — add:**

```markdown
### Controller Verification
- [ ] Check operator logs during reconciliation for the changed code paths
- [ ] Verify status conditions update correctly on the Backstage CR
- [ ] Test with multiple Backstage CRs (if applicable)
- [ ] Delete and recreate a Backstage CR — verify clean reconciliation
```

**Default config changes — add:**

```markdown
### Default Config Verification
- [ ] Deploy a fresh Backstage CR with defaults only
- [ ] Verify changed defaults are applied to the RHDH deployment
- [ ] Compare pod spec / configmaps before and after the change
```

**Test changes — add:**

```markdown
### Tests
- [ ] `make test` — unit tests pass
- [ ] `make integration-test USE_EXISTING_CLUSTER=true USE_EXISTING_CONTROLLER=true` — integration tests pass against live cluster
```

**Dependency changes — add:**

```markdown
### Dependency Review
- [ ] Review `go.mod` diff for major version bumps
- [ ] Check if new dependencies have acceptable licenses
```

**End the checklist with:**

```markdown
### Rollback
When done testing, rollback the operator image:
[rollback commands from Phase 4.7]
```

---

## Phase 6: Offer Automated Verification

Ask the user:

> Would you like me to run some verification commands against the cluster now?

If yes, run the baseline health checks:

```bash
oc get backstage -A
oc get pods -n $OPERATOR_NS
oc logs deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --tail=30
```

If the PR includes test changes, offer to run tests:

```bash
# Only offer — confirm with user before running
# Unit tests (runs locally, safe)
make test

# Integration tests (runs against live cluster)
make integration-test USE_EXISTING_CLUSTER=true USE_EXISTING_CONTROLLER=true PROFILE=rhdh
```

</process>

<action_triggers>

| Trigger | Type | What | Resume When |
|---------|------|------|-------------|
| No CI images found | Wait | CI workflow may still be running | Workflow completes and posts comment |
| Images expired | Stop | PR images past 14-day TTL | Author pushes new commit to retrigger CI |
| No cluster access | Stop | User needs to `oc login` | User logs in and re-runs skill |
| No RHDH instance | Deploy | Deploy via rhdh-test-instance `make install-operator && make deploy-operator` | Operator and Backstage CR are running |

</action_triggers>

<tracking>

## Activity Logging

```bash
$RHDH log add "Review PR #<number> (rhdh-operator): swapped image <tag>, generated checklist" \
  --tag review-pr --tag rhdh-operator

$RHDH log add "PR #<number> review findings: <summary>" \
  --tag review-pr --tag rhdh-operator
```

## Follow-up Todos

```bash
$RHDH todo add "Follow up on PR #<number> finding: <description>" --context "review-pr"

$RHDH todo add "Rollback operator image on cluster after PR #<number> review" --context "review-pr"
```

</tracking>

<success_criteria>

Review is complete when:

- [ ] PR images identified from CI comment
- [ ] Images validated as existing in Quay registry
- [ ] Cluster has RHDH operator running with PR image
- [ ] Operator pod is healthy (no crash loops)
- [ ] Backstage CR reconciles successfully
- [ ] Review checklist generated from diff analysis
- [ ] Rollback instructions documented and shared with user
- [ ] Activity logged

</success_criteria>
