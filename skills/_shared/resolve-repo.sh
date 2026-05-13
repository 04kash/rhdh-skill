#!/usr/bin/env bash
# Resolve the openshift/release repository root for local or remote access.
#
# Provides a single function that all scripts source to determine whether
# to read files from a local checkout or via the GitHub API.
#
# Resolution order:
#   1. Explicit --repo-dir flag (passed via OPENSHIFT_RELEASE_DIR before sourcing)
#   2. OPENSHIFT_RELEASE_DIR environment variable
#   3. Walk up from $PWD looking for the ci-operator sentinel directory
#   4. Fall back to REMOTE mode (GitHub API via gh CLI)
#
# Usage (in consuming scripts):
#   source "$(dirname "${BASH_SOURCE[0]}")/../../_shared/resolve-repo.sh"
#   ROOT=$(resolve_repo_root)
#   if is_remote; then
#     # use gh api ...
#   else
#     # use local files at $ROOT/...
#   fi
#
# No external dependencies beyond bash 3.2+.

set -euo pipefail

# Sentinel path that identifies an openshift/release checkout.
_OR_SENTINEL="ci-operator/config/redhat-developer/rhdh"

# GitHub repository for remote access.
OPENSHIFT_RELEASE_REPO="${OPENSHIFT_RELEASE_REPO:-openshift/release}"

# Resolved root -- populated by resolve_repo_root().
_RESOLVED_ROOT=""

resolve_repo_root() {
  # 1. Explicit override via env var
  if [[ -n "${OPENSHIFT_RELEASE_DIR:-}" ]]; then
    if [[ -d "${OPENSHIFT_RELEASE_DIR}/${_OR_SENTINEL}" ]]; then
      _RESOLVED_ROOT="$OPENSHIFT_RELEASE_DIR"
      echo "$_RESOLVED_ROOT"
      return 0
    else
      echo "WARNING: OPENSHIFT_RELEASE_DIR is set but ${_OR_SENTINEL} not found there" >&2
    fi
  fi

  # 2. Walk up from cwd
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "${dir}/${_OR_SENTINEL}" ]]; then
      _RESOLVED_ROOT="$dir"
      echo "$_RESOLVED_ROOT"
      return 0
    fi
    dir="$(dirname "$dir")"
  done

  # 3. Remote mode
  _RESOLVED_ROOT="REMOTE"
  echo "REMOTE"
  return 0
}

# Returns 0 (true) if we are in remote mode.
is_remote() {
  [[ "$_RESOLVED_ROOT" == "REMOTE" ]]
}

# Returns the full local path for a repo-relative path, or the path as-is
# in remote mode (callers should check is_remote first).
repo_path() {
  local relpath="$1"
  if is_remote; then
    echo "$relpath"
  else
    echo "${_RESOLVED_ROOT}/${relpath}"
  fi
}
