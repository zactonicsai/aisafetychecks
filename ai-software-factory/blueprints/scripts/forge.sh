#!/usr/bin/env bash
# Thin factory CLI. Real implementation wraps tofu, kubectl, aws/az/gcloud.
set -euo pipefail

usage() {
  cat <<'EOF'
forge — Aether Forge developer CLI

  forge ws start <name>       Start local Linux workbench (Colima/Podman)
  forge pkg search <q>        Search internal package repo
  forge pipeline init <tpl>   Copy a pipeline template into the current repo
  forge pipeline run          Trigger CI on current branch
  forge deploy <target>       docker | podman | k3s | aks | gke | eks
  forge rollback <env>        Sync previous Git SHA via GitOps
  forge login                 OIDC device login (Keycloak)

Targets are identical images; only the kube context changes.
EOF
}

cmd="${1:-help}"
case "$cmd" in
  ws)
    echo "[forge] starting workbench ${2:-default} with image harbor.forge.internal/platform/workbench:stable"
    echo "[forge] tip (Mac): colima start --cpu 6 --memory 12 --arch aarch64"
    ;;
  pkg)
    echo "[forge] would query Nexus/Harbor for: ${2:-} ${3:-}"
    ;;
  pipeline)
    echo "[forge] pipeline ${2:-} — templates live in platform/catalog"
    ;;
  deploy)
    target="${2:-k3s}"
    echo "[forge] deploying current image digest to $target (GitOps PR, not ClickOps)"
    ;;
  rollback)
    echo "[forge] rolling back ${2:-stage} to previous approved Git SHA"
    ;;
  login)
    echo "[forge] opening Keycloak device flow…"
    ;;
  *)
    usage
    ;;
esac
