#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="python-demo"
SERVICE="python-web"

echo "Waiting for an external LoadBalancer address..."
for _ in $(seq 1 30); do
  LB_IP="$(kubectl get svc "$SERVICE" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  LB_HOST="$(kubectl get svc "$SERVICE" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)"
  if [[ -n "$LB_IP" || -n "$LB_HOST" ]]; then
    break
  fi
  sleep 2
done

kubectl get svc "$SERVICE" -n "$NAMESPACE" -o wide

echo
if [[ -n "${LB_IP:-}" ]]; then
  echo "Kubernetes LoadBalancer IP: $LB_IP"
  echo "Trying: curl http://${LB_IP}:80/"
  if curl --connect-timeout 3 -fsS "http://${LB_IP}:80/"; then
    echo
    exit 0
  fi
fi

if [[ -n "${LB_HOST:-}" ]]; then
  echo "Kubernetes LoadBalancer hostname: $LB_HOST"
  echo "Trying: curl http://${LB_HOST}:80/"
  if curl --connect-timeout 3 -fsS "http://${LB_HOST}:80/"; then
    echo
    exit 0
  fi
fi

cat <<'MSG'

The Service has a LoadBalancer address, but on Docker Desktop / macOS / Windows
that address may live inside Docker's private network. cloud-provider-kind can
map the LoadBalancer port to a random host port.

Find the cloud-provider-kind / Envoy container and its mapped port:

  docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep kindccm

Look for text similar to:

  0.0.0.0:42381->80/tcp

Then test that HOST port:

  curl http://localhost:42381/

This is a local-development detail. In AWS/Azure/GCP, the cloud provider normally
creates a real external load balancer and Kubernetes reports its address.
MSG
