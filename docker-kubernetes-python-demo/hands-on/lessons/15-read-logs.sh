#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 15: read container logs"
require_context
explain "logs reads standard output and error from containers. A label selector can collect output from every matching Pod."
run kubectl logs -n "${APP_NAMESPACE}" -l app=hello-web --prefix --tail=20
explain "Add -f to follow new log lines continuously; stop following with Control+C."
