---
name: prow-trigger-nightly
description: >-
  Trigger RHDH nightly ProwJobs on demand via the OpenShift CI Gangway REST API.
  Supports both rhdh and rhdh-plugin-export-overlays repos. Use when the user
  wants to trigger, run, kick off, or start a nightly CI job, run an on-demand
  E2E nightly test, list available nightly jobs, or trigger an overlay nightly.
  Also use when the user mentions Gangway, "nightly job", "periodic-ci",
  RC verification, testing a custom image, running CI against a fork, or
  checking available image tags on quay.io.
---
# Trigger Nightly ProwJobs

Trigger RHDH nightly ProwJobs via the OpenShift CI Gangway REST API.

Supports two repositories:
- **rhdh** — the main RHDH application (`periodic-ci-redhat-developer-rhdh-*-nightly`)
- **rhdh-plugin-export-overlays** — plugin export overlays (`periodic-ci-redhat-developer-rhdh-plugin-export-overlays-*-nightly`)

## Script Location

All commands below use paths relative to this skill's directory:
`skills/prow-trigger-nightly/scripts/trigger_nightly_job.py`

## Prerequisites

- Python 3.9+
- `oc` CLI installed (for authentication to OpenShift CI)

## Flow

1. Fetch available jobs and let the user pick one
2. Ask about image override and additional options (fork, alerts)
3. Show the command, confirm, execute, report results

## Step 1: Fetch Jobs and Select

List configured nightly jobs:

```bash
uv run scripts/trigger_nightly_job.py --list
```

Present the jobs in a table with columns: short name and which branches have it. Derive the short name from the job name part after the branch segment (e.g. `e2e-ocp-helm-nightly` -> "OCP Helm"):

| Repo | Job | main | release-1.9 | release-1.8 |
|------|-----|------|-------------|-------------|
| rhdh | OCP Helm | x | x | x |
| rhdh | AKS Helm | x | x | |
| overlays | OCP Helm | x | | |

Then ask the user to describe which job and branch they want in natural language.

### Natural Language Mapping

Map the user's description to the matching full job name from the fetched list. If no branch is mentioned, default to `main`:

**RHDH repo jobs:**
- "ocp helm" / "openshift helm" -> `e2e-ocp-helm-nightly` (not upgrade, not versioned)
- "operator" / "ocp operator" -> `e2e-ocp-operator-nightly` (not auth-providers)
- "helm upgrade" / "upgrade test" -> `e2e-ocp-helm-upgrade-nightly`
- "auth providers" / "authentication" -> `e2e-ocp-operator-auth-providers-nightly`
- "4.17", "4.19", "4.20", "4.21" -> `e2e-ocp-v4-{VERSION}-helm-nightly`
- "aks helm" / "azure helm" -> `e2e-aks-helm-nightly`
- "aks operator" / "azure operator" -> `e2e-aks-operator-nightly`
- "eks helm" / "aws helm" -> `e2e-eks-helm-nightly`
- "eks operator" / "aws operator" -> `e2e-eks-operator-nightly`
- "gke helm" / "google helm" -> `e2e-gke-helm-nightly`
- "gke operator" / "google operator" -> `e2e-gke-operator-nightly`
- "osd" / "osd gcp" -> `e2e-osd-gcp-helm-nightly` or `e2e-osd-gcp-operator-nightly`
- Branch: "1.9", "release 1.9", "1.8 branch" -> match from that branch
- Multiple: "all AKS jobs", "all Operator jobs on main" -> offer to trigger them in sequence

**Overlay repo jobs:**
- "overlay nightly" / "overlay helm" / "overlays nightly" -> `periodic-ci-redhat-developer-rhdh-plugin-export-overlays-main-e2e-ocp-helm-nightly`

### Shared Cluster Constraint (GKE / OSD-GCP only)

GKE and OSD-GCP each share a single cluster — never run two jobs on the same platform simultaneously. Before triggering, warn the user.

## Step 2: Options

**Important:** Overlay repo jobs only support fork overrides (`--org`, `--repo`, `--branch`). Image overrides (`--image-registry`, `--image-repo`, `--tag`) and `--send-alerts` are NOT supported — the script will error if these are passed for an overlay job. If the user doesn't need fork overrides, skip this step and go directly to Step 3.

For RHDH repo jobs, present all options together. The user picks by number — multiple selections allowed (e.g. "2, 5"):

**Image override:**
1. **Default image** — no image flags, use whatever the job is configured with
2. **Custom tag only** — override just the tag, keep default registry and repo
3. **Custom repo + tag** — override image repository and tag, keep default registry (`quay.io`)
4. **Fully custom image** — override registry, repo, and tag

**Additional options:**
5. **Fork override** — run against a fork instead of `redhat-developer/rhdh`
6. **Send Slack alerts** — notify via `--send-alerts`

Constraint: `--image-repo` requires `--tag`, but `--tag` works on its own.

### Follow-up based on selections

**If 2 or 3 selected (quay.io registry)** — fetch available tags and present as numbered options:

```bash
uv run scripts/trigger_nightly_job.py --list-tags [--image-repo <REPO>]
```

Default repo is `rhdh/rhdh-hub-rhel9`. Present the numbered results with a final option to enter a custom tag (e.g. `next`, `latest`). For option 3, also ask for the image repository.

**If 4 selected (non-quay registry)** — ask for all three values (tag fetching not available):
- Registry (e.g. `brew.registry.redhat.io`)
- Image repo (e.g. `rhdh/rhdh-hub-rhel9`)
- Tag (e.g. `1.9`)

**If 5 selected** — ask for:
- GitHub org (`--org`): e.g. `my-github-user`
- Repo name (`--repo`): e.g. `rhdh`
- Branch (`--branch`): e.g. `my-feature-branch`

## Step 3: Confirm and Execute

Show the full command and present final options:

```bash
uv run scripts/trigger_nightly_job.py \
  --job <FULL_JOB_NAME> \
  [--image-registry <REGISTRY>] \
  [--image-repo <REPO>] \
  [--tag <TAG>] \
  [--org <ORG>] \
  [--repo <REPO>] \
  [--branch <BRANCH>] \
  [--send-alerts] \
  [--dry-run]
```

1. **Execute** — run the command as shown
2. **Change something** — go back and modify parameters

After execution, show the API response. If a job URL or ID is returned, display it prominently. On error, help diagnose (common issues: expired token, invalid job name).

## Reference

- Script flags: `-j/--job`, `-l/--list`, `-T/--list-tags`, `-I/--image-registry`, `-q/--image-repo`, `-t/--tag`, `-o/--org`, `-r/--repo`, `-b/--branch`, `-S/--send-alerts`, `-n/--dry-run`
- Dedicated kubeconfig at `~/.config/openshift-ci/kubeconfig` — won't interfere with your current cluster context
- If auth is needed, the script opens a browser for SSO login
- RHDH jobs list: https://prow.ci.openshift.org/configured-jobs/redhat-developer/rhdh
- Overlay jobs list: https://prow.ci.openshift.org/configured-jobs/redhat-developer/rhdh-plugin-export-overlays
- Image tags: https://quay.io/repository/rhdh/rhdh-hub-rhel9?tab=tags

## Related Skills

- **`overlay`**: Manage the rhdh-plugin-export-overlays repository
