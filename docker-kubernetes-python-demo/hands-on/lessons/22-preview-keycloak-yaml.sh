#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 22: render a chart without installing it"
explain "helm template combines chart templates with config/keycloak-values.yaml and prints the Kubernetes YAML. It does not contact or modify the cluster."
run helm template keycloak codecentric/keycloakx \
  --namespace "${KEYCLOAK_NAMESPACE}" \
  --version 7.3.1 \
  --values "${CONFIG_DIR}/keycloak-values.yaml"
explain "Review the rendered StatefulSet, Services, and other objects before installing a chart in important environments."
