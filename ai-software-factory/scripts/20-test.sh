#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
need python3
cd "$ROOT_DIR"

info "Compiling Python"
python3 -m compileall -q app

info "Running simulator unit/API tests"
python3 -m unittest discover -s app/tests -v

info "Checking browser JavaScript and JSON"
if command -v node >/dev/null 2>&1; then
  node --check app/static/app.js
else
  warn "node is not installed; skipped JavaScript syntax check"
fi
python3 -m json.tool platform/keycloak/factory-realm.json >/dev/null

info "Checking Kubernetes YAML structure when kubectl is available"
if command -v kubectl >/dev/null 2>&1; then
  kubectl kustomize infra/kubernetes/overlays/local >/dev/null
else
  warn "kubectl is not installed; skipped kustomize render"
fi

info "Checking shell syntax"
for script in scripts/*.sh scripts/lib/*.sh; do sh -n "$script"; done

info "All available tests passed"
