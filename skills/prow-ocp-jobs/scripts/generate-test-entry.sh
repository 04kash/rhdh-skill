#!/usr/bin/env bash
# Generate a new e2e-ocp-vX-Y-helm-nightly test entry YAML block.
#
# Clones a reference entry and substitutes the OCP version in:
#   - as (test name)
#   - cluster_claim.version
#   - steps.env.OC_CLIENT_VERSION
#
# Outputs the block to stdout for review before insertion.
#
# Supports both local openshift/release checkout and remote GitHub API access.
#
# Usage:
#   generate-test-entry.sh --version 4.22 --branch main [--reference 4.21] [--repo-dir <path>]
#
# Requires: yq (v4+), jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../_shared/fetch-yaml.sh"

CONFIG_DIR="ci-operator/config/redhat-developer/rhdh"
OCP_VERSION=""
BRANCH=""
REFERENCE_VERSION=""

# Parse --repo-dir first, then skill-specific args
init_repo "$@"
set -- "${SCRIPT_ARGS[@]+"${SCRIPT_ARGS[@]}"}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version|-v)    OCP_VERSION="$2"; shift 2 ;;
    --branch|-b)     BRANCH="$2"; shift 2 ;;
    --reference|-r)  REFERENCE_VERSION="$2"; shift 2 ;;
    --config-dir|-d) CONFIG_DIR="$2"; shift 2 ;;
    *) echo "Usage: $0 --version X.Y --branch <name> [--reference X.Y] [--config-dir <path>] [--repo-dir <path>]" >&2; exit 1 ;;
  esac
done

[[ -n "$OCP_VERSION" ]] || { echo "ERROR: --version is required (e.g., --version 4.22)" >&2; exit 1; }
[[ -n "$BRANCH" ]] || { echo "ERROR: --branch is required (e.g., --branch main)" >&2; exit 1; }

if ! echo "$OCP_VERSION" | grep -qE '^[0-9]+\.[0-9]+$'; then
  echo "ERROR: Version must be in X.Y format (e.g., 4.22), got: ${OCP_VERSION}" >&2
  exit 1
fi

command -v yq &>/dev/null || { echo "ERROR: yq (v4+) required" >&2; exit 1; }

MAJOR="${OCP_VERSION%%.*}"
MINOR="${OCP_VERSION#*.}"

# Locate the config file
PREFIX="redhat-developer-rhdh-"
CONFIG_FILE_NAME="${PREFIX}${BRANCH}.yaml"

FILES=$(list_yaml_files "$CONFIG_DIR" "${CONFIG_FILE_NAME}") || { echo "ERROR: Failed to find config file for branch ${BRANCH}" >&2; exit 1; }
CONFIG_FILE=$(echo "$FILES" | head -1)

[[ -n "$CONFIG_FILE" ]] || { echo "ERROR: Config file not found for branch '${BRANCH}'" >&2; exit 1; }

CONTENT=$(fetch_yaml "$CONFIG_FILE") || { echo "ERROR: Failed to read ${CONFIG_FILE}" >&2; exit 1; }

# Check if test entry already exists
EXISTING=$(echo "$CONTENT" | yq -o=json "[.tests[] | select(.as == \"e2e-ocp-v${MAJOR}-${MINOR}-helm-nightly\")]" 2>/dev/null || true)
if [[ -n "$EXISTING" && "$EXISTING" != "[]" ]]; then
  echo "ERROR: Test entry e2e-ocp-v${MAJOR}-${MINOR}-helm-nightly already exists in ${BRANCH}" >&2
  exit 1
fi

# Find a reference entry to clone
if [[ -n "$REFERENCE_VERSION" ]]; then
  REF_MAJOR="${REFERENCE_VERSION%%.*}"
  REF_MINOR="${REFERENCE_VERSION#*.}"
  REF_NAME="e2e-ocp-v${REF_MAJOR}-${REF_MINOR}-helm-nightly"
else
  # Find the latest versioned OCP helm-nightly entry
  REF_NAME=$(echo "$CONTENT" | yq -o=json '[.tests[] | select(.as | test("^e2e-ocp-v[0-9]+-[0-9]+-helm-nightly$")) | .as] | sort | last' 2>/dev/null | tr -d '"' || true)
fi

if [[ -z "$REF_NAME" || "$REF_NAME" == "null" ]]; then
  echo "ERROR: No reference OCP test entry found in ${BRANCH}" >&2
  exit 1
fi

# Extract reference version from the entry name
REF_VER_MATCH=$(echo "$REF_NAME" | grep -oE 'v[0-9]+-[0-9]+' || true)
if [[ -z "$REF_VER_MATCH" ]]; then
  echo "ERROR: Could not extract version from reference entry: ${REF_NAME}" >&2
  exit 1
fi
REF_MAJOR="${REF_VER_MATCH#v}"
REF_MAJOR="${REF_MAJOR%%-*}"
REF_MINOR="${REF_VER_MATCH##*-}"

echo "# Generated test entry for OCP ${OCP_VERSION}" >&2
echo "# Based on reference: ${REF_NAME}" >&2
echo "# Insert this block into the tests: list in ${CONFIG_FILE_NAME}" >&2
echo "# Place it adjacent to other e2e-ocp-v*-helm-nightly entries" >&2
echo "# Then run: make update" >&2
echo "" >&2

# Extract the reference entry and substitute version fields
echo "$CONTENT" | yq -o=json ".tests[] | select(.as == \"${REF_NAME}\")" 2>/dev/null | \
  jq --arg new_name "e2e-ocp-v${MAJOR}-${MINOR}-helm-nightly" \
     --arg new_ver "${OCP_VERSION}" \
     --arg new_oc "stable-${OCP_VERSION}" \
     '.as = $new_name | .cluster_claim.version = $new_ver | .steps.env.OC_CLIENT_VERSION = $new_oc' | \
  yq -P '.'
