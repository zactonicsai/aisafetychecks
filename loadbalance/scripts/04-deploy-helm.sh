#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
helm lint "$ROOT/helm/python-demo"
helm upgrade --install python-demo "$ROOT/helm/python-demo" --namespace python-demo --create-namespace --wait --timeout 2m
kubectl -n python-demo get pods,svc
