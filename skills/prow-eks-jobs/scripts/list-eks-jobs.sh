#!/usr/bin/env bash
# List EKS test entries in RHDH CI config files.
# Thin wrapper around the shared list-k8s-test-configs.sh.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/../../_shared/list-k8s-test-configs.sh" --pattern "^e2e-eks-" "$@"
