#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 03: create the kind cluster"
explain "kind reads kind-config.yaml and creates one control-plane container plus two worker containers. The port mapping connects Mac port 8080 to Kubernetes NodePort 30080."
need docker
need kind
if kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  explain "The cluster already exists, so this rerun leaves it unchanged."
else
  run kind create cluster --name "${CLUSTER_NAME}" --config "${CONFIG_DIR}/kind-config.yaml"
fi
run kind get clusters
run docker ps --filter "name=${CLUSTER_NAME}"
