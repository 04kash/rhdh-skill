---
name: prow-aks-jobs
description: >-
  List AKS test entries in RHDH ci-operator config files and update the AKS
  Kubernetes version per branch. Use when listing e2e-aks tests, changing
  MAPT_KUBERNETES_VERSION for AKS, or checking which AKS K8s version each
  release branch uses.
---
# RHDH AKS Prow Job Management

List AKS test entries and update the K8s version used by AKS MAPT clusters.

## When to Use

- List which AKS test entries exist per RHDH release branch
- Check which K8s version each branch is configured to use
- Update the AKS K8s version after a lifecycle check
- The version is set per branch via `MAPT_KUBERNETES_VERSION` in each CI config file

## Prerequisites

- `yq` (v4+) for listing tests
- Works from any directory (auto-detects local checkout or uses GitHub API)
- For updating versions: requires a local `openshift/release` checkout

## Listing Tests

```bash
bash "${SKILL_DIR}/scripts/list-aks-jobs.sh"
```

### Filter by branch

```bash
bash "${SKILL_DIR}/scripts/list-aks-jobs.sh" --branch main
```

### Override repo location

```bash
bash "${SKILL_DIR}/scripts/list-aks-jobs.sh" --repo-dir /path/to/openshift/release
```

## Updating the Version (requires local checkout)

The K8s version is set per branch as the `MAPT_KUBERNETES_VERSION` env var in each CI config file:

```text
ci-operator/config/redhat-developer/rhdh/redhat-developer-rhdh-<branch>.yaml
```

Each AKS test entry has `MAPT_KUBERNETES_VERSION` under `steps.env`. Update all AKS test entries in the file -- each branch typically has multiple AKS tests that should use the same version. To update, use the `Edit` tool to change the value for the target branch. Example:

```yaml
  steps:
    env:
      MAPT_KUBERNETES_VERSION: "1.35"
```

Verify the MAPT image tag in the ref YAML is compatible with the new K8s version:

```text
ci-operator/step-registry/redhat-developer/rhdh/aks/mapt/create/redhat-developer-rhdh-aks-mapt-create-ref.yaml
```

**NOTE**: Each branch can use a different K8s version. `make update` is NOT required for version changes.

## Related Skills

- **`lifecycle-aks`**: Check which K8s versions are supported before updating
