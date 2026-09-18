#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
PROVIDER=${1:-}
validate_provider "$PROVIDER"
need kubectl
IAC=$(iac_command)
DIR="$ROOT_DIR/infra/terraform/$PROVIDER"

cd "$DIR"
case "$PROVIDER" in
  aws)
    need aws
    OVERLAY=eks
    aws eks update-kubeconfig --region "$("$IAC" output -raw region)" --name "$("$IAC" output -raw cluster_name)"
    ;;
  azure)
    need az
    OVERLAY=aks
    az aks get-credentials --resource-group "$("$IAC" output -raw resource_group_name)" --name "$("$IAC" output -raw cluster_name)" --overwrite-existing
    ;;
  gcp)
    need gcloud
    OVERLAY=gke
    gcloud container clusters get-credentials "$("$IAC" output -raw cluster_name)" --region "$("$IAC" output -raw region)" --project "$("$IAC" output -raw project_id)"
    ;;
esac

if grep -R -Eq 'REPLACE_|replace-with' "$ROOT_DIR/infra/kubernetes/overlays/$OVERLAY"; then
  fail "Replace the image placeholders in infra/kubernetes/overlays/$OVERLAY/kustomization.yaml with the pushed registry image, preferably by digest."
fi

info "Current Kubernetes context"
kubectl config current-context
kubectl auth can-i create deployments --namespace ai-factory || true
kubectl apply -k "$ROOT_DIR/infra/kubernetes/overlays/$OVERLAY"
kubectl -n ai-factory rollout status deployment/factory-simulator --timeout=180s
