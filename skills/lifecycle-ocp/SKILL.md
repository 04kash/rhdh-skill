---
name: lifecycle-ocp
description: >-
  Check OCP version lifecycle status including support phases (Full,
  Maintenance, EUS) and end-of-life dates, using the Red Hat Product
  Life Cycles API. Cross-references with RHDH compatibility. Use when
  asking about OCP version support, EUS phases, or whether a specific
  OCP version is still supported. Supports OCP 4.x and future 5.x+
---
# Check OCP Version Lifecycle

Query the Red Hat Product Life Cycles API for OCP version support status.

## When to Use

- Check if a specific OCP version is still supported
- See which OCP versions are in Full Support, Maintenance, or EUS
- Determine which OCP versions RHDH supports (cross-reference)
- Before adding or removing OCP cluster pools or CI test entries

## Prerequisites

- Python 3.9+
- Internet connectivity to reach `https://access.redhat.com`

## Usage

Show all OCP versions:

```bash
uv run scripts/check_ocp_lifecycle.py
```

### Check a specific OCP version

```bash
uv run scripts/check_ocp_lifecycle.py --version 4.16
```

### JSON output

```bash
uv run scripts/check_ocp_lifecycle.py --json
```

## Output

### OCP Lifecycle Table

| Column | Description |
|--------|-------------|
| VERSION | OCP minor version (e.g., `4.16`) |
| OCP_SUPP | `yes` if OCP version has upstream support (any phase) |
| RHDH_SUPP | `yes` if any active RHDH release supports this OCP version |
| PHASE | Current OCP lifecycle phase |
| GA_DATE | OCP General Availability date |
| END_DATE | Latest end-of-support date across all OCP phases |

The **RHDH_SUPP** column is the key indicator for CI coverage decisions. An OCP version should only have cluster pools and test entries if `RHDH_SUPP=yes`.

## Key Concepts

- **Full Support**: Actively supported, receives patches and security updates
- **Maintenance Support**: Past full support, still receives critical fixes
- **Extended Update Support (EUS)**: Extended lifecycle for specific versions
- **End of life**: No longer receiving any updates

An OCP version can be OCP-supported but not RHDH-supported (e.g., an older EUS version that RHDH has dropped).

## Data Sources

- **OCP lifecycle**: `https://access.redhat.com/product-life-cycles/api/v1/products?name=Red+Hat+OpenShift+Container+Platform`
- **RHDH compatibility**: Fetched from RHDH lifecycle API for the RHDH_SUPP cross-reference

## Related Skills

- **`lifecycle-rhdh`**: Check RHDH release lifecycle (GA dates, support phases, OCP compatibility)
- **`prow-ocp-coverage`**: Cross-reference lifecycle data with pools and job configs
- **`prow-ocp-pools`**: List and generate OCP cluster pool configurations
- **`prow-ocp-jobs`**: List, generate, add, and remove OCP test entries
