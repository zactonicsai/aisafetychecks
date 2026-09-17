#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 07: inspect system Pods"
require_context
explain "A Pod is Kubernetes's smallest deployable unit. -A means all namespaces, including kube-system where DNS and control components run."
run kubectl get pods -A -o wide
explain "Namespaces divide one cluster into named work areas."
run kubectl get namespaces
