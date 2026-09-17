#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 13: create a Service"
require_context
explain "Pods can be replaced and receive new IPs. A Service supplies one stable virtual address and selects Pods whose label is app=hello-web."
run kubectl apply -f "${CONFIG_DIR}/service.yaml"
run kubectl get service hello-web -n "${APP_NAMESPACE}" -o wide
explain "EndpointSlices show the actual Pod addresses currently behind the Service."
run kubectl get endpointslice -n "${APP_NAMESPACE}" -l kubernetes.io/service-name=hello-web -o wide
