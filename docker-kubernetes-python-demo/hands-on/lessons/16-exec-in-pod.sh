#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 16: execute a command inside a container"
require_context
POD="$(kubectl get pods -n "${APP_NAMESPACE}" -l app=hello-web -o jsonpath='{.items[0].metadata.name}')"
explain "exec asks the kubelet to start a process in an existing container. This noninteractive example prints the hostname and first lines of nginx's page."
run kubectl exec -n "${APP_NAMESPACE}" "${POD}" -- sh -c 'hostname; head -n 5 /usr/share/nginx/html/index.html'
explain "For an interactive shell, use: kubectl exec -it -n hands-on POD_NAME -- /bin/sh"
