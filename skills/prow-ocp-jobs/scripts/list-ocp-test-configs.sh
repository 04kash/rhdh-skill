#!/usr/bin/env bash
# List OCP versions used in RHDH CI test configs.
#
# Extracts OCP versions from cluster_claim.version (the source of truth),
# not from test names. This catches all OCP-targeted tests, including ones
# that don't encode the version in their name.
#
# Supports both local openshift/release checkout and remote GitHub API access.
#
# Usage:
#   list-ocp-test-configs.sh [--branch <name>] [--repo-dir <path>]
#
# Requires: yq (v4+), jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../_shared/fetch-yaml.sh"

CONFIG_DIR="ci-operator/config/redhat-developer/rhdh"
FILTER_BRANCH=""

# Parse --repo-dir first, then skill-specific args
init_repo "$@"
set -- "${SCRIPT_ARGS[@]+"${SCRIPT_ARGS[@]}"}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch|-b)     FILTER_BRANCH="$2"; shift 2 ;;
    --config-dir|-d) CONFIG_DIR="$2"; shift 2 ;;
    *) echo "Usage: $0 [--branch <name>] [--config-dir <path>] [--repo-dir <path>]" >&2; exit 1 ;;
  esac
done

command -v yq &>/dev/null || { echo "ERROR: yq (v4+) required" >&2; exit 1; }

PREFIX="redhat-developer-rhdh-"
FILES=$(list_yaml_files "$CONFIG_DIR" "${PREFIX}*.yaml") || { echo "ERROR: Failed to list config files" >&2; exit 1; }

while IFS= read -r config_file; do
  [[ -z "$config_file" ]] && continue
  branch=$(extract_branch "$PREFIX" "$config_file")
  [[ -n "$FILTER_BRANCH" && "$branch" != "$FILTER_BRANCH" ]] && continue

  content=$(fetch_yaml "$config_file" 2>/dev/null) || continue

  # Extract OCP versions from cluster_claim.version (the source of truth)
  versions=$(echo "$content" | yq -o=json -I=0 \
    '[.tests[] | select(.cluster_claim.version != null) | .cluster_claim.version] | unique | .[]' \
    2>/dev/null | tr -d '"' | sort -V || true)

  [[ -z "$versions" ]] && continue

  echo ""
  echo "=== Branch: ${branch} ==="
  printf "  %-45s %-13s %-30s %-10s\n" TEST_NAME OCP_VERSION CRON OPTIONAL
  printf "  %-45s %-13s %-30s %-10s\n" --------- ----------- ---- --------

  echo "$content" | yq -o=json -I=0 \
    '[.tests[] | select(.cluster_claim.version != null)]' 2>/dev/null | \
    jq -r '.[] | [.as, .cluster_claim.version, (.cron//"N/A"), (.optional//false|tostring)] | @tsv' | sort | \
    while IFS=$'\t' read -r name ver cron opt; do
      printf "  %-45s %-13s %-30s %-10s\n" "$name" "$ver" "$cron" "$opt"
    done

  echo ""
  echo "  OCP versions tested: $(echo "$versions" | tr '\n' ' ')"
done <<< "$FILES"
