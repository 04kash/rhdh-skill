---
name: lifecycle
description: >-
  Check version lifecycle and support status for platforms and integrations
  used by RHDH. Covers OCP, AKS, EKS, GKE, RHDH releases, RHBK, Quay,
  PostgreSQL, and any Red Hat product via the Product Life Cycles API.
  Use when asking about version support, EOL dates, GA dates, support
  phases, or planning version upgrades. Also use for "is X still
  supported", "what versions should we test", or "when does X reach EOL".
---
# Version Lifecycle Checks

Check version lifecycle and support status for platforms and integrations used by RHDH.

## Prerequisites

- Python 3.9+
- Internet connectivity for API access
- For configured K8s version display (AKS/EKS): local `openshift/release` checkout or `gh` CLI

## Identify Platform

What platform or integration lifecycle do you need to check?

| Query matches | Workflow |
|---|---|
| "OCP", "OpenShift version", "OpenShift EOL", "OpenShift support" | `workflows/check-ocp.md` |
| "RHDH version", "Developer Hub release", "is RHDH 1.x supported" | `workflows/check-rhdh.md` |
| "AKS", "Azure Kubernetes" | `workflows/check-aks.md` |
| "EKS", "Amazon EKS" | `workflows/check-eks.md` |
| "GKE", "Google Kubernetes" | `workflows/check-gke.md` |
| "RHBK", "Keycloak", "Red Hat Build of Keycloak", "Quay", any Red Hat product | `workflows/check-redhat.md` |
| "PostgreSQL", "Postgres", "PG", "database versions" | `workflows/check-pg.md` |
| "all platforms", "full lifecycle check" | Run all workflows in sequence |

After reading the workflow, follow it exactly.

## Available Scripts

All scripts support `--help` for usage details and `--json` for structured output.

| Script | Purpose |
|--------|---------|
| `scripts/check_ocp_lifecycle.py` | OCP version lifecycle with EUS phases |
| `scripts/check_rhdh_lifecycle.py` | RHDH release lifecycle with OCP compatibility |
| `scripts/check_lifecycle.py` | Generic Red Hat product (RHBK, Quay, etc.) |
| `scripts/check_aks_lifecycle.py` | AKS K8s version lifecycle |
| `scripts/check_eks_lifecycle.py` | EKS K8s version lifecycle |
| `scripts/check_gke_lifecycle.py` | GKE K8s version lifecycle |
| `scripts/check_pg_lifecycle.py` | PostgreSQL lifecycle across cloud providers |

## Related Skills

- **`prow`**: Manage Prow CI job configurations for RHDH in openshift/release
