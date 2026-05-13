---
name: lifecycle-rhdh
description: >-
  Check RHDH release lifecycle status including GA dates, support phases,
  and OCP compatibility per release. Use when asking about RHDH version
  support, EOL dates, which RHDH releases are active, or which OCP
  versions a specific RHDH release supports. Also use for release
  planning or when deciding whether to upgrade.
---
# Check RHDH Release Lifecycle

Query the Red Hat Product Life Cycles API for RHDH release information.

## When to Use

- Check if a specific RHDH version is still supported
- Find GA dates, Full Support and Maintenance Support end dates
- See which OCP versions each RHDH release supports
- Determine which RHDH releases are currently active
- Plan release branch decommissioning

## Prerequisites

- Python 3.9+
- Internet connectivity to reach `https://access.redhat.com`

## Usage

Show all RHDH releases:

```bash
uv run scripts/check_rhdh_lifecycle.py
```

### Check a specific RHDH version

```bash
uv run scripts/check_rhdh_lifecycle.py --version 1.9
```

### Show only active releases

```bash
uv run scripts/check_rhdh_lifecycle.py --active-only
```

### JSON output

```bash
uv run scripts/check_rhdh_lifecycle.py --json
```

## Output

### RHDH Lifecycle Table

| Column | Description |
|--------|-------------|
| VERSION | RHDH release version (e.g., `1.9`) |
| SUPPORTED | `yes` or `no` |
| TYPE | `Full Support`, `Maintenance Support`, or `End of life` |
| GA_DATE | General Availability date |
| FULL_SUPPORT_END | End of Full Support phase |
| MAINTENANCE_END | End of Maintenance Support phase |
| SUPPORTED_OCP | OCP versions this RHDH release officially supports |

After the table, a summary shows:

- The union of OCP versions supported across all active RHDH releases
- Per-release OCP support breakdown

## Data Source

**RHDH lifecycle**: `https://access.redhat.com/product-life-cycles/api/v1/products?name=Red+Hat+Developer+Hub`

The `openshift_compatibility` field is the authoritative source for which OCP versions each RHDH release supports.

## Related Skills

- **`lifecycle-ocp`**: Check OCP version lifecycle (support phases, EUS status)
- **`prow-decommission-release`**: Decommission CI jobs for an end-of-life RHDH release
- **`prow-ocp-coverage`**: Cross-reference RHDH and OCP lifecycle data with CI coverage
