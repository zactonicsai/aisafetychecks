#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 90: remove applications but keep the cluster"
require_context
explain "helm uninstall removes objects managed by the Keycloak release. Namespace deletion removes everything remaining inside that namespace."
if helm status keycloak -n "${KEYCLOAK_NAMESPACE}" >/dev/null 2>&1; then
  run helm uninstall keycloak -n "${KEYCLOAK_NAMESPACE}"
fi
run kubectl delete namespace "${KEYCLOAK_NAMESPACE}" --ignore-not-found
run kubectl delete namespace "${APP_NAMESPACE}" --ignore-not-found
run kubectl get namespaces
