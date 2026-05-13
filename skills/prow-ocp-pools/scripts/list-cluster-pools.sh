#!/usr/bin/env bash
# List RHDH Hive ClusterPool configurations.
#
# Supports both local openshift/release checkout and remote GitHub API access.
#
# Usage:
#   list-cluster-pools.sh [--repo-dir <path>] [--pool-dir <path>]
#
# Requires: yq (v4+)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../_shared/fetch-yaml.sh"

POOL_DIR="clusters/hosted-mgmt/hive/pools/rhdh"

# Parse --repo-dir first, then skill-specific args
init_repo "$@"
set -- "${SCRIPT_ARGS[@]+"${SCRIPT_ARGS[@]}"}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pool-dir|-d) POOL_DIR="$2"; shift 2 ;;
    *) echo "Usage: $0 [--pool-dir <path>] [--repo-dir <path>]" >&2; exit 1 ;;
  esac
done

command -v yq &>/dev/null || { echo "ERROR: yq (v4+) required" >&2; exit 1; }

echo "=== RHDH Cluster Pools ==="
echo ""
printf "  %-8s  %-50s  %-5s  %-5s  %-8s  %-70s  %s\n" \
  "VERSION" "POOL_NAME" "SIZE" "MAX" "RUNNING" "IMAGE_SET" "FILENAME"
printf "  %-8s  %-50s  %-5s  %-5s  %-8s  %-70s  %s\n" \
  "-------" "---------" "----" "---" "-------" "---------" "--------"

FILES=$(list_yaml_files "$POOL_DIR" "*_clusterpool.yaml") || { echo "ERROR: Failed to list pool files" >&2; exit 1; }

# Collect and sort output by version
OUTPUT=""
while IFS= read -r pool_file; do
  [[ -z "$pool_file" ]] && continue

  content=$(fetch_yaml "$pool_file" 2>/dev/null) || continue

  ver=$(echo "$content" | yq '.metadata.labels.version' 2>/dev/null) || true
  [[ -z "$ver" || "$ver" == "null" ]] && continue

  pool_name=$(echo "$content" | yq '.metadata.name // "unknown"' 2>/dev/null) || true
  size=$(echo "$content" | yq '.spec.size // 0' 2>/dev/null) || true
  max=$(echo "$content" | yq '.spec.maxSize // 0' 2>/dev/null) || true
  running=$(echo "$content" | yq '.spec.runningCount // 0' 2>/dev/null) || true
  image_set=$(echo "$content" | yq '.spec.imageSetRef.name // "N/A"' 2>/dev/null) || true
  filename=$(basename "$pool_file")

  OUTPUT+="$(printf "  %-8s  %-50s  %-5s  %-5s  %-8s  %-70s  %s" \
    "$ver" "$pool_name" "$size" "$max" "$running" "$image_set" "$filename")"$'\n'
done <<< "$FILES"

# Sort by version
echo "$OUTPUT" | sort -t'.' -k1,1n -k2,2n
