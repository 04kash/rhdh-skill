#!/usr/bin/env bash
# Fetch YAML files from the openshift/release repository (local or remote).
#
# Provides helper functions for listing and reading YAML files from either
# a local checkout or the GitHub API, abstracting the dual-mode access
# pattern used by all prow-* and lifecycle-* skills.
#
# Usage (in consuming scripts):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "${SCRIPT_DIR}/../../_shared/fetch-yaml.sh"
#   init_repo "$@"  # parses --repo-dir, resolves root
#
#   # List YAML files matching a glob in a repo directory
#   list_yaml_files "ci-operator/config/redhat-developer/rhdh" "redhat-developer-rhdh-*.yaml"
#
#   # Read a single YAML file (local path or remote repo path)
#   fetch_yaml "ci-operator/config/redhat-developer/rhdh/redhat-developer-rhdh-main.yaml"
#
# Requires: curl (remote mode), gh (remote mode)

set -euo pipefail

_SHARED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SHARED_DIR}/resolve-repo.sh"

# Parse --repo-dir from args and resolve the repo root.
# Strips --repo-dir from the args and exports remaining args as SCRIPT_ARGS.
# Call this at the top of each consuming script.
init_repo() {
  local args=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo-dir)
        export OPENSHIFT_RELEASE_DIR="$2"
        shift 2
        ;;
      *)
        args+=("$1")
        shift
        ;;
    esac
  done
  SCRIPT_ARGS=("${args[@]+"${args[@]}"}")
  resolve_repo_root >/dev/null
}

# List YAML files in a directory, one path per line.
#
# In local mode, returns absolute paths.
# In remote mode, returns repo-relative paths.
#
# Args:
#   $1 - repo-relative directory path (e.g., "ci-operator/config/redhat-developer/rhdh")
#   $2 - filename glob pattern (e.g., "redhat-developer-rhdh-*.yaml")
list_yaml_files() {
  local dir_path="$1"
  local pattern="$2"

  if is_remote; then
    # Use GitHub Contents API to list directory, filter by pattern
    local api_path="repos/${OPENSHIFT_RELEASE_REPO}/contents/${dir_path}"
    gh api "$api_path" --jq ".[] | select(.name | test(\"${pattern}\")) | .path" 2>/dev/null || {
      echo "ERROR: Failed to list ${dir_path} via GitHub API" >&2
      return 1
    }
  else
    local full_dir
    full_dir="$(repo_path "$dir_path")"
    if [[ ! -d "$full_dir" ]]; then
      echo "ERROR: Directory not found: ${full_dir}" >&2
      return 1
    fi
    # Convert glob pattern to find-compatible form and return repo-relative paths
    for f in "${full_dir}"/${pattern}; do
      [[ -f "$f" ]] || continue
      echo "$f"
    done
  fi
}

# Fetch a single YAML file's content to stdout.
#
# In local mode, the argument is an absolute path (as returned by list_yaml_files).
# In remote mode, the argument is a repo-relative path.
#
# Args:
#   $1 - file path (absolute local or repo-relative for remote)
fetch_yaml() {
  local file_path="$1"

  if is_remote; then
    # Fetch via GitHub raw content
    local raw_url="https://raw.githubusercontent.com/${OPENSHIFT_RELEASE_REPO}/HEAD/${file_path}"
    curl -sL --fail "$raw_url" || {
      echo "ERROR: Failed to fetch ${file_path} from GitHub" >&2
      return 1
    }
  else
    if [[ ! -f "$file_path" ]]; then
      echo "ERROR: File not found: ${file_path}" >&2
      return 1
    fi
    cat "$file_path"
  fi
}

# Extract the branch/filename stem from a config file path.
# Works for both absolute local paths and repo-relative remote paths.
#
# Example:
#   extract_branch "redhat-developer-rhdh-" ".../redhat-developer-rhdh-main.yaml"
#   => "main"
#   extract_branch "redhat-developer-rhdh-" ".../redhat-developer-rhdh-release-1.9.yaml"
#   => "release-1.9"
extract_branch() {
  local prefix="$1"
  local filepath="$2"
  local filename
  filename="$(basename "$filepath")"
  echo "$filename" | sed "s/^${prefix}//;s/\\.yaml$//"
}

# Print configured MAPT_KUBERNETES_VERSION per branch from CI config files.
#
# Shared helper used by lifecycle-aks and lifecycle-eks scripts.
#
# Args:
#   $1 - repo-relative config dir (e.g., "ci-operator/config/redhat-developer/rhdh")
#   $2 - test name regex pattern (e.g., "^e2e-aks-")
#   $3 - (optional) repo-relative path to MAPT ref YAML
#
# Requires: yq (v4+)
print_configured_versions() {
  local config_dir="$1"
  local test_pattern="$2"
  local mapt_ref="${3:-}"

  local mapt_tag=""
  if [[ -n "$mapt_ref" ]]; then
    local ref_content
    ref_content="$(fetch_yaml "$mapt_ref" 2>/dev/null)" || true
    if [[ -n "$ref_content" ]]; then
      mapt_tag=$(echo "$ref_content" | grep 'tag:' | awk '{print $2}' | head -1 || true)
    fi
  fi

  if ! command -v yq &>/dev/null; then
    echo "WARNING: yq not available, skipping configured versions" >&2
    return 0
  fi

  local prefix="redhat-developer-rhdh-"
  local files
  files="$(list_yaml_files "$config_dir" "${prefix}*.yaml")" || return 0
  [[ -z "$files" ]] && return 0

  echo "Configured MAPT_KUBERNETES_VERSION per branch:"
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    local branch
    branch="$(extract_branch "$prefix" "$f")"
    local content
    content="$(fetch_yaml "$f" 2>/dev/null)" || continue
    local ver
    ver=$(echo "$content" | yq -o=json "[.tests[] | select(.as | test(\"${test_pattern}\")) | .steps.env.MAPT_KUBERNETES_VERSION // \"N/A\"] | unique | .[]" 2>/dev/null | sort -u | paste -sd',' - || echo "N/A")
    [[ -z "$ver" ]] && ver="N/A"
    echo "  ${branch}: ${ver}"
  done <<< "$files"
  [[ -n "$mapt_tag" ]] && echo "MAPT image: mapt:${mapt_tag}"
  echo ""
}
