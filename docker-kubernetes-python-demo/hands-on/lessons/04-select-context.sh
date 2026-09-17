#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 04: understand and select kubeconfig context"
explain "A context combines a cluster address, credentials, and an optional default namespace. Selecting it prevents kubectl from sending commands to the wrong cluster."
run kubectl config get-contexts
run kubectl config use-context "${CONTEXT_NAME}"
run kubectl config current-context
explain "The kubeconfig file is normally at ~/.kube/config. The next command shows only the active context without displaying every stored cluster."
run kubectl config view --minify
