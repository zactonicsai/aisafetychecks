#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
need kubectl

NAMESPACE=${NAMESPACE:-ai-factory}
DEPLOYMENT=${DEPLOYMENT:-factory-simulator}
info "Showing rollout history before rollback"
kubectl -n "$NAMESPACE" rollout history deployment/"$DEPLOYMENT"
info "Rolling back one revision"
kubectl -n "$NAMESPACE" rollout undo deployment/"$DEPLOYMENT"
kubectl -n "$NAMESPACE" rollout status deployment/"$DEPLOYMENT" --timeout=180s
warn "For GitOps-managed environments, also revert the desired image digest in Git or Argo CD will reconcile it forward again."

