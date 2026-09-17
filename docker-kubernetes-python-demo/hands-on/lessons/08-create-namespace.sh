#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 08: apply a Namespace manifest"
require_context
explain "apply is declarative: kubectl reads namespace.yaml and asks the API server to make reality match the file. Reapplying the same file is safe."
run kubectl apply -f "${CONFIG_DIR}/namespace.yaml"
run kubectl get namespace "${APP_NAMESPACE}" --show-labels
explain "Set the current context's default namespace so later commands without -n use hands-on."
run kubectl config set-context --current --namespace="${APP_NAMESPACE}"
