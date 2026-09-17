#!/usr/bin/env bash
set -euo pipefail
CLUSTER_NAME="${CLUSTER_NAME:-python-demo}"
kind load docker-image python-demo-web:1.0.0 --name "$CLUSTER_NAME"
kind load docker-image python-demo-api:1.0.0 --name "$CLUSTER_NAME"
echo "Images loaded into kind cluster '$CLUSTER_NAME'."
