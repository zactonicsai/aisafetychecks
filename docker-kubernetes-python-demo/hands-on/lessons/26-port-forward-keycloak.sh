#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 26: port-forward Keycloak"
require_context
POD="$(kubectl get pod -n "${KEYCLOAK_NAMESPACE}" -l app.kubernetes.io/instance=keycloak -o jsonpath='{.items[0].metadata.name}')"
[[ -n "${POD}" ]] || { echo "No Keycloak Pod found. Run lessons 23 and 24." >&2; exit 1; }
run kubectl wait --for=condition=Ready "pod/${POD}" -n "${KEYCLOAK_NAMESPACE}" --timeout=300s
USER="$(kubectl get secret keycloak-admin -n "${KEYCLOAK_NAMESPACE}" -o jsonpath='{.data.username}' | base64 --decode)"
PASS="$(kubectl get secret keycloak-admin -n "${KEYCLOAK_NAMESPACE}" -o jsonpath='{.data.password}' | base64 --decode)"
explain "port-forward creates a temporary local tunnel. It runs until Control+C and does not create a permanent Service exposure."
printf 'URL: http://127.0.0.1:8081/admin/\nUsername: %s\nPassword: %s\n' "${USER}" "${PASS}"
run kubectl port-forward -n "${KEYCLOAK_NAMESPACE}" "pod/${POD}" 8081:8080
