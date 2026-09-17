#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 19: ConfigMap versus Secret"
require_context
explain "A ConfigMap stores non-sensitive settings in YAML."
run kubectl apply -f "${CONFIG_DIR}/configmap.yaml"
run kubectl get configmap lesson-settings -n "${APP_NAMESPACE}" -o yaml
explain "For a Secret, generate a manifest from literals and pipe it to apply. The password is not written to a project file."
DEMO_PASSWORD="$(openssl rand -hex 12)"
kubectl create secret generic lesson-credentials \
  -n "${APP_NAMESPACE}" \
  --from-literal=username=student \
  --from-literal=password="${DEMO_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -
run kubectl get secret lesson-credentials -n "${APP_NAMESPACE}"
explain "Secret values are hidden in normal output. They are base64-encoded, not automatically encrypted. See config/secret-example.yaml for structure only."
