#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker build -t python-demo-web:1.0.0 "$ROOT/apps/web"
docker build -t python-demo-api:1.0.0 "$ROOT/apps/api"
docker images | grep 'python-demo-' || true
