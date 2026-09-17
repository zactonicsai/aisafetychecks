#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 11: wait for rollout"
require_context
explain "rollout status watches until the Deployment has the desired number of available Pods or the timeout expires."
run kubectl rollout status deployment/hello-web -n "${APP_NAMESPACE}" --timeout=180s
explain "rollout history lists revisions. A new Pod-template change creates a new revision."
run kubectl rollout history deployment/hello-web -n "${APP_NAMESPACE}"
