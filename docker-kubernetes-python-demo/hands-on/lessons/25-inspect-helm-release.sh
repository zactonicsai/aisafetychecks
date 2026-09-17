#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 25: inspect a Helm release"
require_context
explain "list shows installed releases. status shows one release's state and resources. get values shows your overrides; get manifest shows the generated YAML stored for the release."
run helm list -n "${KEYCLOAK_NAMESPACE}"
run helm status keycloak -n "${KEYCLOAK_NAMESPACE}"
run helm get values keycloak -n "${KEYCLOAK_NAMESPACE}"
run helm get manifest keycloak -n "${KEYCLOAK_NAMESPACE}"
