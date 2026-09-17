#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 10: create a Deployment"
require_context
explain "First, client-side dry-run validates and renders the file without changing the cluster."
run kubectl apply --dry-run=client -f "${CONFIG_DIR}/deployment.yaml" -o yaml
explain "The real apply stores the desired Deployment. Its controller creates a ReplicaSet, which creates two Pods."
run kubectl apply -f "${CONFIG_DIR}/deployment.yaml"
run kubectl get deployment,replicaset,pods -n "${APP_NAMESPACE}"
