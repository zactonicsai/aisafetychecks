#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="python-demo"
NAMESPACE="python-demo"
RELEASE="python-demo"
CHART="./helm/python-demo"

if ! kind get clusters | grep -qx "$CLUSTER_NAME"; then
  echo "kind cluster '$CLUSTER_NAME' does not exist."
  echo "Run ./scripts/01-create-cluster.sh first."
  exit 1
fi

if ! command -v cloud-provider-kind >/dev/null 2>&1; then
  echo "cloud-provider-kind is not installed."
  echo "Run ./scripts/07-install-loadbalancer-helper.sh first."
  exit 1
fi

cat <<'MSG'
STEP 1 - Start the local load-balancer controller

Open a SECOND terminal and keep this command running:

  cloud-provider-kind --enable-lb-port-mapping

On some systems it may require elevated privileges:

  sudo cloud-provider-kind --enable-lb-port-mapping

Then return to this terminal and continue.
MSG

printf "\nPress Enter after cloud-provider-kind is running... "
read -r _

# The worker node normally hosts our workload. Remove the exclusion label from
# control-plane nodes as well so this lab still works if a workload lands there.
kubectl label node "${CLUSTER_NAME}-control-plane" \
  node.kubernetes.io/exclude-from-external-load-balancers- \
  --overwrite >/dev/null 2>&1 || true

echo "Updating the Helm release: web=LoadBalancer, api=ClusterIP..."
helm upgrade --install "$RELEASE" "$CHART" \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --set web.serviceType=LoadBalancer \
  --set api.serviceType=ClusterIP \
  --wait \
  --timeout 2m

echo
echo "Services:"
kubectl get services -n "$NAMESPACE" -o wide

echo
cat <<'MSG'
The python-web Service should now show TYPE=LoadBalancer.
The EXTERNAL-IP can take a few seconds to appear.

Watch it with:
  kubectl get svc python-web -n python-demo -w

Then run:
  ./scripts/09-test-loadbalancer.sh
MSG
