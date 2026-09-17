#!/usr/bin/env bash
set -euo pipefail

HANDSON_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${HANDSON_ROOT}/config"
CLUSTER_NAME="docker-k8"
CONTEXT_NAME="kind-${CLUSTER_NAME}"
APP_NAMESPACE="hands-on"
KEYCLOAK_NAMESPACE="keycloak"

title() {
  printf '\n=== %s ===\n' "$1"
}

explain() {
  printf '%s\n' "$1"
}

run() {
  printf '\n$'
  printf ' %q' "$@"
  printf '\n\n'
  "$@"
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing command: %s\n' "$1" >&2
    exit 1
  }
}

require_context() {
  local current
  current="$(kubectl config current-context 2>/dev/null || true)"
  if [[ "${current}" != "${CONTEXT_NAME}" ]]; then
    printf 'Expected context %s but current context is %s\n' "${CONTEXT_NAME}" "${current:-none}" >&2
    printf 'Run lesson 04 before continuing.\n' >&2
    exit 1
  fi
}
