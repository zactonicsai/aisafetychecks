#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
need kind
need kubectl

if kind get clusters 2>/dev/null | grep -qx ai-factory; then
  info "kind cluster ai-factory already exists"
else
  info "Creating kind cluster"
  kind create cluster --name ai-factory --config "$ROOT_DIR/developer-workspace/kind.yaml"
fi
kubectl config use-context kind-ai-factory
kubectl cluster-info

