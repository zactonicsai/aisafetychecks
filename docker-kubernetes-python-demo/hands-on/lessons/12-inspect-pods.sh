#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 12: get and describe Pods"
require_context
explain "Labels connect resources. The selector app=hello-web returns only this application's Pods."
run kubectl get pods -n "${APP_NAMESPACE}" -l app=hello-web -o wide --show-labels
POD="$(kubectl get pods -n "${APP_NAMESPACE}" -l app=hello-web -o jsonpath='{.items[0].metadata.name}')"
explain "describe combines configuration, live status, conditions, and recent events. It is usually the first command for a Pending or failing Pod."
run kubectl describe pod "${POD}" -n "${APP_NAMESPACE}"
