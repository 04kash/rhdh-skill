#!/usr/bin/env bash
# List K8s platform test entries in RHDH CI config files.
#
# Shared script used by prow-aks-jobs, prow-eks-jobs, and prow-gke-jobs skills.
# Supports both local openshift/release checkout and remote GitHub API access.
#
# Usage:
#   list-k8s-test-configs.sh --pattern <regex> [--branch <name>] [--repo-dir <path>]
#
# Examples:
#   list-k8s-test-configs.sh --pattern "^e2e-aks-"
#   list-k8s-test-configs.sh --pattern "^e2e-eks-" --branch main
#   list-k8s-test-configs.sh --pattern "^e2e-gke-"
#
# Requires: yq (v4+), jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/fetch-yaml.sh"

CONFIG_DIR="ci-operator/config/redhat-developer/rhdh"
PATTERN=""
FILTER_BRANCH=""

# Parse --repo-dir first, then skill-specific args
init_repo "$@"
set -- "${SCRIPT_ARGS[@]+"${SCRIPT_ARGS[@]}"}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pattern|-p)    PATTERN="$2"; shift 2 ;;
    --branch|-b)     FILTER_BRANCH="$2"; shift 2 ;;
    --config-dir|-d) CONFIG_DIR="$2"; shift 2 ;;
    *) echo "Usage: $0 --pattern <regex> [--branch <name>] [--config-dir <path>] [--repo-dir <path>]" >&2; exit 1 ;;
  esac
done

[[ -n "$PATTERN" ]] || { echo "ERROR: --pattern is required" >&2; exit 1; }
command -v yq &>/dev/null || { echo "ERROR: yq (v4+) required" >&2; exit 1; }

PREFIX="redhat-developer-rhdh-"
HAS_MAPT_VERSION=false

FILES=$(list_yaml_files "$CONFIG_DIR" "${PREFIX}*.yaml") || { echo "ERROR: Failed to list config files" >&2; exit 1; }

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  branch=$(extract_branch "$PREFIX" "$f")
  [[ -n "$FILTER_BRANCH" && "$branch" != "$FILTER_BRANCH" ]] && continue

  content=$(fetch_yaml "$f" 2>/dev/null) || continue
  entries=$(echo "$content" | yq -o=json -I=0 "[.tests[] | select(.as | test(\"${PATTERN}\"))]" 2>/dev/null || true)
  [[ -z "$entries" || "$entries" == "[]" ]] && continue

  # Check if any entry has MAPT_KUBERNETES_VERSION
  has_ver=$(echo "$entries" | jq -r '[.[] | .steps.env.MAPT_KUBERNETES_VERSION // empty] | length')

  echo ""
  echo "=== Branch: ${branch} ==="
  if [[ "$has_ver" -gt 0 ]]; then
    HAS_MAPT_VERSION=true
    printf "  %-40s %-13s %-30s %-10s\n" TEST_NAME K8S_VERSION CRON OPTIONAL
    printf "  %-40s %-13s %-30s %-10s\n" --------- ----------- ---- --------
    echo "$entries" | jq -r '.[] | [.as, (.steps.env.MAPT_KUBERNETES_VERSION//"N/A"), (.cron//"N/A"), (.optional//false|tostring)] | @tsv' | sort | \
      while IFS=$'\t' read -r name ver cron opt; do
        printf "  %-40s %-13s %-30s %-10s\n" "$name" "$ver" "$cron" "$opt"
      done
  else
    printf "  %-40s %-30s %-10s\n" TEST_NAME CRON OPTIONAL
    printf "  %-40s %-30s %-10s\n" --------- ---- --------
    echo "$entries" | jq -r '.[] | [.as, (.cron//"N/A"), (.optional//false|tostring)] | @tsv' | sort | \
      while IFS=$'\t' read -r name cron opt; do
        printf "  %-40s %-30s %-10s\n" "$name" "$cron" "$opt"
      done
  fi
done <<< "$FILES"

echo ""
if [[ "$HAS_MAPT_VERSION" == "true" ]]; then
  echo "K8s version source: MAPT_KUBERNETES_VERSION in steps.env per test entry" >&2
else
  echo "K8s version: managed outside CI config (static cluster)" >&2
fi
