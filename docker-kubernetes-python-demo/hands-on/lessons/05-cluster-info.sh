#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 05: contact the Kubernetes API"
require_context
explain "cluster-info asks the selected API server for its main endpoints. If this fails, investigate Docker, the context, or kubeconfig before deploying an app."
run kubectl cluster-info
explain "The short raw request below asks the API server health endpoint directly through kubectl."
run kubectl get --raw=/readyz
