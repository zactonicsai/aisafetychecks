#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 06: inspect nodes"
require_context
explain "Nodes are the machines where Pods run. In kind, these machines are Docker containers. -o wide adds IP address, runtime, and Kubernetes version."
run kubectl get nodes -o wide
explain "describe gives detailed capacity, labels, conditions, and recent events for one node."
run kubectl describe node "${CLUSTER_NAME}-control-plane"
