---
name: prow-ocp-pools
description: >-
  List existing RHDH OCP Hive ClusterPool configurations and generate new pool
  YAML for a target OCP version, with imageSetRef aligned from other pools in
  the openshift/release repository. Covers OCP pools only, not K8s platforms
---
# RHDH OCP Cluster Pool Management

List and manage OCP Hive ClusterPool configurations for RHDH in the `openshift/release` repository. This skill covers OCP cluster pools only -- K8s platform clusters (AKS, EKS, GKE) are provisioned via MAPT and OSD-GCP via a separate claim workflow.

## When to Use

Use this skill when you need to:
- List current RHDH cluster pools and their OCP versions
- Generate a new cluster pool YAML for a new OCP version
- Review cluster pool capacity (size, maxSize, runningCount)
- Remove a cluster pool for an end-of-life OCP version

## Prerequisites

- `yq` (v4+) must be available for YAML parsing
- For listing: works from any directory (auto-detects local checkout or uses GitHub API)
- For generating: requires a local `openshift/release` checkout (writes files)

## Listing Cluster Pools

Run the bundled script (works from any directory):

```bash
bash "${SKILL_DIR}/scripts/list-cluster-pools.sh"
```

### Override repo location

```bash
bash "${SKILL_DIR}/scripts/list-cluster-pools.sh" --repo-dir /path/to/openshift/release
```

### Output format

The script outputs a table with columns:

| Column | Description |
|--------|-------------|
| VERSION | OCP minor version (e.g., `4.18`) |
| POOL_NAME | Hive ClusterPool resource name |
| SIZE | Desired pool size |
| MAX | Maximum pool size |
| RUNNING | Number of clusters kept running (hibernation bypass) |
| IMAGE_SET | ClusterImageSet reference name |
| FILENAME | Pool YAML filename |

## Generating a New Cluster Pool (requires local checkout)

Use the bundled generation script:

```bash
bash "${SKILL_DIR}/scripts/generate-cluster-pool.sh" --version 4.22
```

### With a specific reference pool

```bash
bash "${SKILL_DIR}/scripts/generate-cluster-pool.sh" --version 4.22 --reference 4.21
```

### Preview without writing (dry-run)

```bash
bash "${SKILL_DIR}/scripts/generate-cluster-pool.sh" --version 4.22 --dry-run
```

### What the script does

1. **Looks up the `imageSetRef`** by scanning ALL cluster pools across the entire `clusters/hosted-mgmt/hive/pools/` directory (not just RHDH pools). This ensures alignment with other teams' pools for the same OCP version.
2. **Copies an existing RHDH pool** as a structural template (defaults to the latest, or use `--reference` to pick one).
3. **Updates version-specific fields**: `version`, `version_lower`, `version_upper`, pool `name`, and `imageSetRef`.
4. **Sets conservative sizing**: `size: 1`, `maxSize: 2`, no `runningCount`.
5. **Writes the file** directly to `clusters/hosted-mgmt/hive/pools/rhdh/`.
6. **Prints the generated YAML** to stdout for review.

### Error cases

- If no existing pool in the repo uses the target OCP version, the script **errors out** rather than guessing a patch version.
- If an RHDH pool for the target version already exists, the script errors out.

## Removing a Cluster Pool

To remove a cluster pool for an end-of-life OCP version:

1. Delete the `*_clusterpool.yaml` file
2. Verify no CI jobs still reference this pool's version via `cluster_claim.version`
3. Use the `prow-ocp-jobs` skill to check for and remove any remaining OCP test entries

## File Layout

All cluster pool files live in:
```
clusters/hosted-mgmt/hive/pools/rhdh/
├── OWNERS
├── admins_rhdh-cluster-pool_rbac.yaml
├── rhdh-aws-us-east-2.yaml
└── rhdh-ocp-<major>-<minor>-0-amd64-aws-us-east-2_clusterpool.yaml  # One per OCP version
```

## Key Details

- **Region**: All RHDH pools use `us-east-2`
- **Architecture**: `amd64`
- **Base domain**: `rhdh-qe.devcluster.openshift.com`
- **Worker nodes**: `m6i.2xlarge`
- **Credentials**: `rhdh-aws-credentials` secret
- **Namespace**: `rhdh-cluster-pool`

## Related Skills

- **`lifecycle-ocp`**: Check which OCP versions are supported before adding/removing pools
- **`prow-ocp-jobs`**: Manage test entries that consume these pools
- **`prow-ocp-coverage`**: Cross-reference pool coverage with lifecycle data
