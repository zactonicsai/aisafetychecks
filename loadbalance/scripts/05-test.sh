#!/usr/bin/env bash
set -euo pipefail
NAMESPACE=python-demo
cleanup() {
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null || true
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT
kubectl -n "$NAMESPACE" port-forward svc/python-web 18080:80 >/tmp/python-demo-web-pf.log 2>&1 & WEB_PID=$!
kubectl -n "$NAMESPACE" port-forward svc/python-api 18081:80 >/tmp/python-demo-api-pf.log 2>&1 & API_PID=$!
sleep 3
echo "--- Web health ---"
curl -fsS http://127.0.0.1:18080/health; echo
echo "--- API GET ---"
curl -fsS 'http://127.0.0.1:18081/api/hello?name=Kubernetes'; echo
echo "--- API POST ---"
curl -fsS -X POST http://127.0.0.1:18081/api/hello -H 'Content-Type: application/json' -d '{"name":"Docker"}'; echo
echo "All tests passed."
