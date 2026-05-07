# Reference: Cluster Provisioning via rhdh-test-instance

Two paths for getting an RHDH cluster running, depending on whether you already have cluster access.

<provision_via_pr>

## Provision a cluster via rhdh-test-instance PR (no cluster needed)

This uses the rhdh-test-instance PR workflow — Prow CI provisions an OpenShift cluster, deploys RHDH with Keycloak, and posts back the URL + credentials. No local clone required.

**Step 1: Find or create a PR on rhdh-test-instance**

```bash
TEST_INSTANCE_REPO="redhat-developer/rhdh-test-instance"

# Check for an existing open PR you can use
gh pr list --repo $TEST_INSTANCE_REPO --state open --limit 5
```

If no suitable PR exists, create one:

```bash
# Fork and create a no-op PR (e.g., update README or add a comment)
gh repo fork $TEST_INSTANCE_REPO --clone=false
gh pr create --repo $TEST_INSTANCE_REPO \
  --title "test: PR review environment for rhdh-operator PR #$PR_NUMBER" \
  --body "Temporary PR to provision a test cluster for reviewing rhdh-operator PR #$PR_NUMBER" \
  --head <your-fork-branch>
```

**Step 2: Trigger deployment**

```bash
TEST_PR=<pr-number-on-rhdh-test-instance>

gh pr comment $TEST_PR --repo $TEST_INSTANCE_REPO \
  --body "/test deploy operator 1.9 4h"  # Replace 1.9 with the current RHDH minor version — check rhdh-operator Makefile VERSION
```

**Step 3: Wait for Prow to post credentials**

The Prow job takes several minutes. Monitor:

- Prow status: https://prow.ci.openshift.org/?repo=redhat-developer%2Frhdh-test-instance&type=presubmit&job=pull-ci-redhat-developer-rhdh-test-instance-main-deploy

Poll the PR for the bot's response:

```bash
# Check for deployment comment (contains RHDH URL and credentials)
gh pr view $TEST_PR --repo $TEST_INSTANCE_REPO --json comments \
  --jq '.comments[] | select(.body | test("RHDH URL|Deployed")) | .body' | tail -1
```

The bot response includes:
- RHDH URL
- OpenShift Console URL
- Cluster credentials (from Vault)
- Cluster availability window

**Step 4: Log in to the provisioned cluster**

```bash
oc login <cluster-url-from-bot> -u <username> -p <password>
```

</provision_via_pr>

<deploy_on_existing_cluster>

## Deploy RHDH on an existing cluster (cluster accessible, no RHDH)

If `oc whoami` works but no RHDH operator is running, deploy one using rhdh-test-instance locally.

Locate the repo:

```bash
RHDH_TEST_INSTANCE=""
for candidate in \
  ../rhdh-test-instance \
  ~/Documents/something-about-skills/rhdh-test-instance \
  ~/src/rhdh/rhdh-test-instance \
  ~/rhdh-test-instance; do
  if [ -f "$candidate/Makefile" ] && [ -f "$candidate/deploy.sh" ]; then
    RHDH_TEST_INSTANCE="$(cd "$candidate" && pwd)"
    break
  fi
done
echo "rhdh-test-instance: ${RHDH_TEST_INSTANCE:-NOT FOUND}"
```

If not found, clone it:

```bash
git clone https://github.com/redhat-developer/rhdh-test-instance.git
RHDH_TEST_INSTANCE="$(pwd)/rhdh-test-instance"
```

Deploy:

```bash
cd $RHDH_TEST_INSTANCE

# Configure secrets
cp .env.example .env
# Edit .env with Keycloak credentials if needed

# Install operator (one-time, runs in container — needs podman)
# Replace 1.9 with the current RHDH minor version — check rhdh-operator Makefile VERSION
make install-operator VERSION=1.9

# Deploy RHDH instance
make deploy-operator VERSION=1.9
```

Wait for readiness:

```bash
oc get pods -n rhdh -w
make url
```

</deploy_on_existing_cluster>
