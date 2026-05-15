#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["ruamel.yaml"]
# ///
"""List AKS test entries in RHDH CI config files."""

import sys

from rhdh_prow.k8s_configs import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--pattern", "^e2e-aks-", *sys.argv[1:]]
    main()
