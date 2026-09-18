#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
need kind
need kubectl

ENGINE=docker
command -v docker >/dev/null 2>&1 || ENGINE=podman
need "$ENGINE"

info "Building local image with $ENGINE"
"$ENGINE" build -f "$ROOT_DIR/Containerfile" -t ai-software-factory-simulator:local "$ROOT_DIR"

info "Loading image into kind"
kind load docker-image ai-software-factory-simulator:local --name ai-factory

info "Applying the local overlay"
kubectl apply -k "$ROOT_DIR/infra/kubernetes/overlays/local"
kubectl -n ai-factory rollout status deployment/factory-simulator --timeout=120s
kubectl -n ai-factory get pods,services

info "Run: kubectl -n ai-factory port-forward service/factory-simulator 8080:80"

