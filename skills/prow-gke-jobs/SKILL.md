---
name: prow-gke-jobs
description: >-
  List GKE test entries in RHDH ci-operator config files. Use when listing
  e2e-gke tests or checking which branches have GKE test entries. Unlike
  AKS/EKS, GKE uses a pre-existing static cluster -- version upgrades are
  performed via the GCP Console.
---
# RHDH GKE Prow Job Management

List GKE test entries across RHDH release branches.

Unlike AKS/EKS which set `MAPT_KUBERNETES_VERSION` in CI config files, GKE uses
a pre-existing static cluster. Version upgrades are performed via the GCP Console.

## When to Use

- List which GKE test entries exist per RHDH release branch
- Verify test coverage across branches

## Prerequisites

- `yq` (v4+) for listing tests
- Works from any directory (auto-detects local checkout or uses GitHub API)

## Listing Tests

```bash
bash "${SKILL_DIR}/scripts/list-gke-jobs.sh"
```

### Filter by branch

```bash
bash "${SKILL_DIR}/scripts/list-gke-jobs.sh" --branch main
```

### Override repo location

```bash
bash "${SKILL_DIR}/scripts/list-gke-jobs.sh" --repo-dir /path/to/openshift/release
```

## Cluster Version Management

The GKE cluster details (name, region, project) are stored in the `rhdh` secret
under `test-credentials`. To check the current version and perform upgrades,
use the GCP Console:

1. Open the [GKE clusters page](https://console.cloud.google.com/kubernetes/list/overview)
2. Select the correct project
3. Click on the cluster to view version details and available upgrades

**NOTE**: `make update` is NOT required -- the version lives on the cluster, not in CI config.

## Related Skills

- **`lifecycle-gke`**: Check which K8s versions are supported before upgrading
