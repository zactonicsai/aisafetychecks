#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 17: scale a Deployment"
require_context
explain "scale changes the Deployment's desired replica count to five. The controller creates the missing Pods."
run kubectl scale deployment/hello-web -n "${APP_NAMESPACE}" --replicas=5
run kubectl rollout status deployment/hello-web -n "${APP_NAMESPACE}" --timeout=180s
run kubectl get pods -n "${APP_NAMESPACE}" -l app=hello-web -o wide
explain "Important: a later kubectl apply of deployment.yaml sets replicas back to the file's value of two. YAML remains the source of truth."
