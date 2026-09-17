#!/usr/bin/env bash
set -euo pipefail
for cmd in docker kind kubectl helm curl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: $cmd is not installed or not in PATH"; exit 1; }
done
docker info >/dev/null 2>&1 || { echo "ERROR: Docker is not running"; exit 1; }
echo "Prerequisites look good."
docker --version
kind --version
kubectl version --client
helm version --short
