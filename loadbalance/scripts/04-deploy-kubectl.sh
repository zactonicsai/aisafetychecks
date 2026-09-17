#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kubectl create namespace python-demo --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "$ROOT/k8s/web.yaml"
kubectl apply -f "$ROOT/k8s/api.yaml"
kubectl -n python-demo rollout status deployment/python-web --timeout=120s
kubectl -n python-demo rollout status deployment/python-api --timeout=120s
kubectl -n python-demo get pods,svc
