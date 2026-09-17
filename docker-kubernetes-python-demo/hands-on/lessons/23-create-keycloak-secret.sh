#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 23: create Keycloak namespace and credentials"
require_context
explain "The namespace command uses dry-run output piped to apply, making it rerunnable."
kubectl create namespace "${KEYCLOAK_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
if kubectl get secret keycloak-admin -n "${KEYCLOAK_NAMESPACE}" >/dev/null 2>&1; then
  explain "keycloak-admin already exists, so the password is not rotated on a rerun."
else
  PASSWORD="$(openssl rand -base64 32 | tr -d '\n' | tr '/+' '_-' | cut -c1-28)"
  run kubectl create secret generic keycloak-admin \
    -n "${KEYCLOAK_NAMESPACE}" \
    --from-literal=username=admin \
    --from-literal=password="${PASSWORD}"
fi
run kubectl get secret keycloak-admin -n "${KEYCLOAK_NAMESPACE}"
explain "The Keycloak values file refers to keys username and password in this Secret."
