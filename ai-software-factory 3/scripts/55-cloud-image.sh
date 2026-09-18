#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
PROVIDER=${1:-}
validate_provider "$PROVIDER"
need docker
IAC=$(iac_command)
DIR="$ROOT_DIR/infra/terraform/$PROVIDER"
TAG=${IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || printf 'dev')}

cd "$DIR"
REGISTRY=$("$IAC" output -raw registry_url)

case "$PROVIDER" in
  aws)
    need aws
    AWS_REGION=$("$IAC" output -raw region)
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$(printf '%s' "$REGISTRY" | cut -d/ -f1)"
    ;;
  azure)
    need az
    az acr login --name "$(printf '%s' "$REGISTRY" | cut -d. -f1)"
    ;;
  gcp)
    need gcloud
    gcloud auth configure-docker "$(printf '%s' "$REGISTRY" | cut -d/ -f1)" --quiet
    ;;
esac

IMAGE_REF="$REGISTRY:$TAG"
info "Building and pushing $IMAGE_REF"
docker buildx build --platform "${PLATFORMS:-linux/amd64,linux/arm64}" --push -f "$ROOT_DIR/Containerfile" -t "$IMAGE_REF" "$ROOT_DIR"
info "Update the selected Kubernetes overlay to use this image, preferably its resolved sha256 digest: $IMAGE_REF"

