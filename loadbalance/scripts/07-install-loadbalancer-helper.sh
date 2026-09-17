#!/usr/bin/env bash
set -euo pipefail

# Local kind clusters do not include a cloud load balancer by themselves.
# cloud-provider-kind watches Service objects of type LoadBalancer and creates
# local load-balancer containers that act like a tiny cloud provider.

if command -v cloud-provider-kind >/dev/null 2>&1; then
  echo "cloud-provider-kind is already installed:"
  command -v cloud-provider-kind
  exit 0
fi

if command -v brew >/dev/null 2>&1; then
  echo "Installing cloud-provider-kind with Homebrew..."
  brew install cloud-provider-kind
elif command -v go >/dev/null 2>&1; then
  echo "Homebrew was not found. Installing cloud-provider-kind with Go..."
  go install sigs.k8s.io/cloud-provider-kind@latest
  GOPATH_BIN="$(go env GOPATH)/bin"
  echo
  echo "Installed under: ${GOPATH_BIN}"
  echo "If cloud-provider-kind is not on PATH, run:"
  echo "  export PATH=\"${GOPATH_BIN}:\$PATH\""
else
  echo "cloud-provider-kind is not installed."
  echo "Install it with one of these methods:"
  echo "  brew install cloud-provider-kind"
  echo "or"
  echo "  go install sigs.k8s.io/cloud-provider-kind@latest"
  exit 1
fi

echo
command -v cloud-provider-kind || true
