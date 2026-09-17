#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER_NAME="${CLUSTER_NAME:-python-demo}"
if kind get clusters | grep -qx "$CLUSTER_NAME"; then
  echo "kind cluster '$CLUSTER_NAME' already exists."
else
  kind create cluster --name "$CLUSTER_NAME" --config "$ROOT/kind-config.yaml"
fi
kubectl config use-context "kind-$CLUSTER_NAME"
kubectl cluster-info
kubectl get nodes -o wide
