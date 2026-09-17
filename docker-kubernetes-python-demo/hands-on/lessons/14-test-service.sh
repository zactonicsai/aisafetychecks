#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 14: test the NodePort path"
require_context
explain "Traffic flows from Mac localhost:8080 to kind node port 30080, then to the Service, and finally to nginx port 80 in a selected Pod."
run curl --fail --show-error --silent --include http://127.0.0.1:8080/
explain "Open the same URL in a browser with: open http://127.0.0.1:8080"
