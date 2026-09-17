#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 18: test self-healing"
require_context
POD="$(kubectl get pods -n "${APP_NAMESPACE}" -l app=hello-web -o jsonpath='{.items[0].metadata.name}')"
explain "Deleting one Pod removes actual state, but the Deployment still requests the same replica count. Its controller creates a replacement."
run kubectl delete pod "${POD}" -n "${APP_NAMESPACE}"
run kubectl wait --for=condition=Ready pod -n "${APP_NAMESPACE}" -l app=hello-web --timeout=180s
run kubectl get pods -n "${APP_NAMESPACE}" -l app=hello-web
explain "Compare the new Pod names with the deleted name: ${POD}"
