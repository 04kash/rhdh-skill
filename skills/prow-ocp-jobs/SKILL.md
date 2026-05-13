---
name: prow-ocp-jobs
description: >-
  List, generate, add, and remove OCP-versioned test entries (e2e-ocp-*) in RHDH
  ci-operator config files. Covers only OCP cluster-claim tests, not K8s platform
  tests (AKS, EKS, GKE, OSD)
---
# RHDH OCP Prow Job Management

Manage OCP-specific test entries in RHDH ci-operator configuration files. This skill covers tests that use OCP cluster claims (`cluster_claim.version`), not K8s platform tests (AKS, EKS, GKE, OSD-GCP) which use different provisioning workflows.

## When to Use

Use this skill when you need to:
- List which OCP versions have helm-nightly test entries per RHDH release branch
- Add a new OCP version test entry to a config file
- Remove an end-of-life OCP version test entry from a config file
- Generate a test entry YAML block for review before adding it

## Prerequisites

- `yq` (v4+) must be available for YAML parsing
- For listing: works from any directory (auto-detects local checkout or uses GitHub API)
- For generating/adding/removing: requires a local `openshift/release` checkout

## Important: Branch Terminology

**"Branch" refers to the RHDH product branch encoded in the config filename** (e.g., `main`, `release-1.8`, `release-1.9`), **NOT** a git branch in the `openshift/release` repo. All CI config files live on the `main` git branch of `openshift/release`.

| Config filename | Product branch | Git branch |
|----------------|----------------|------------|
| `redhat-developer-rhdh-main.yaml` | `main` | `main` |
| `redhat-developer-rhdh-release-1.9.yaml` | `release-1.9` | `main` |
| `redhat-developer-rhdh-release-1.8.yaml` | `release-1.8` | `main` |

## Listing OCP Test Configs

Run the bundled script (works from any directory):

```bash
bash "${SKILL_DIR}/scripts/list-ocp-test-configs.sh"
```

### Filter by product branch

```bash
bash "${SKILL_DIR}/scripts/list-ocp-test-configs.sh" --branch main
```

### Override repo location

```bash
bash "${SKILL_DIR}/scripts/list-ocp-test-configs.sh" --repo-dir /path/to/openshift/release
```

### Output format

The script extracts OCP versions from `cluster_claim.version` in each test entry (the source of truth), not from test names.

```
=== Branch: main ===
TEST_NAME                                      OCP_VERSION   CRON                           OPTIONAL
e2e-ocp-helm                                   4.18          N/A                            false
e2e-ocp-helm-nightly                           4.18          0 4 * * *                      true
e2e-ocp-v4-19-helm-nightly                     4.19          0 5 * * TUE,THU,SAT,SUN        true

  OCP versions tested: 4.18 4.19
```

## Generating a Test Entry

Use the bundled script to generate a new test entry YAML block:

```bash
bash "${SKILL_DIR}/scripts/generate-test-entry.sh" --version 4.22 --branch main
```

### With a specific reference version

```bash
bash "${SKILL_DIR}/scripts/generate-test-entry.sh" --version 4.22 --branch main --reference 4.21
```

The script outputs a ready-to-insert YAML block based on an existing versioned test entry with all version-specific values substituted.

## Adding a Test Entry (requires local checkout)

After generating and reviewing the test entry:

1. Open the target config file (e.g., `ci-operator/config/redhat-developer/rhdh/redhat-developer-rhdh-main.yaml`)
2. Insert the new test entry in the `tests:` list, **before** `zz_generated_metadata:`
3. Place it adjacent to other `e2e-ocp-v*-helm-nightly` entries for readability
4. Run `make update` to regenerate Prow job configs
5. Verify the generated jobs in `ci-operator/jobs/redhat-developer/rhdh/`

### Test entry fields to update

When creating a test entry for OCP version `X.Y`:

| Field | Value |
|-------|-------|
| `as` | `e2e-ocp-vX-Y-helm-nightly` |
| `cluster_claim.version` | `"X.Y"` |
| `steps.env.OC_CLIENT_VERSION` | `stable-X.Y` |

## Removing a Test Entry (requires local checkout)

To remove an OCP version test entry:

1. Open the target config file
2. Remove the entire test block where `as: e2e-ocp-vX-Y-helm-nightly`
3. Run `make update` to regenerate Prow job configs
4. Verify the removed jobs are no longer in `ci-operator/jobs/redhat-developer/rhdh/`

**IMPORTANT**: When removing an OCP version, check **all** product branch configs (main, release-1.9, release-1.8, etc.) for entries that need removal.

## After Any Change

Always run `make update` after modifying CI config files:

```bash
make update
```

This regenerates:
- Prow job configs in `ci-operator/jobs/`
- `zz_generated_metadata` sections
- Other downstream artifacts

## File Layout

CI config files live in:
```
ci-operator/config/redhat-developer/rhdh/
├── redhat-developer-rhdh-main.yaml
├── redhat-developer-rhdh-release-1.8.yaml
└── redhat-developer-rhdh-release-1.9.yaml
```

Generated Prow jobs go to:
```
ci-operator/jobs/redhat-developer/rhdh/
├── redhat-developer-rhdh-main-presubmits.yaml
├── redhat-developer-rhdh-main-periodics.yaml
└── ...
```

## Related Skills

- **`lifecycle-ocp`**: Check which OCP versions are supported before adding/removing
- **`prow-ocp-pools`**: Manage cluster pools (needed before adding test entries)
- **`prow-ocp-coverage`**: Cross-reference all coverage data
