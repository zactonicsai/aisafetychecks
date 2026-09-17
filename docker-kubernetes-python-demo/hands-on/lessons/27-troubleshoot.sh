#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 27: troubleshooting sequence"
require_context
explain "Start broad, then narrow: nodes, Pods, events, descriptions, logs, Services, endpoints, and Helm releases. Commands ending with || true allow the report to continue when a component is absent."
run kubectl get nodes -o wide
run kubectl get pods -A -o wide
run kubectl get events -A --sort-by=.metadata.creationTimestamp
kubectl describe deployment hello-web -n "${APP_NAMESPACE}" || true
kubectl logs -n "${APP_NAMESPACE}" -l app=hello-web --prefix --tail=50 || true
kubectl get services,endpointslices -A || true
helm list -A || true
kubectl describe pods -n "${KEYCLOAK_NAMESPACE}" || true
kubectl logs -n "${KEYCLOAK_NAMESPACE}" -l app.kubernetes.io/instance=keycloak --tail=100 || true
