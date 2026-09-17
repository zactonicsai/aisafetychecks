#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 99: delete the entire kind cluster"
explain "This removes the docker-k8 Kubernetes node containers and everything stored inside the cluster. Project files and Docker Desktop remain."
run kind delete cluster --name "${CLUSTER_NAME}"
run kind get clusters
explain "Rebuild later by starting again at lesson 03."
