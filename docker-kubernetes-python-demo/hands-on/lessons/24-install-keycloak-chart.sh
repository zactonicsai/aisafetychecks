#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 24: install Keycloak with Helm"
require_context
explain "upgrade --install is rerunnable: it creates release keycloak when absent and upgrades it when present. --wait waits for readiness; --timeout limits the wait."
run helm upgrade --install keycloak codecentric/keycloakx \
  --namespace "${KEYCLOAK_NAMESPACE}" \
  --version 7.3.1 \
  --values "${CONFIG_DIR}/keycloak-values.yaml" \
  --wait \
  --timeout 10m
run kubectl get statefulset,pods,services -n "${KEYCLOAK_NAMESPACE}" -o wide
