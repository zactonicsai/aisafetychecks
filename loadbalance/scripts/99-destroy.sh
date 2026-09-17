#!/usr/bin/env bash
set -euo pipefail
CLUSTER_NAME="${CLUSTER_NAME:-python-demo}"
kind delete cluster --name "$CLUSTER_NAME"
