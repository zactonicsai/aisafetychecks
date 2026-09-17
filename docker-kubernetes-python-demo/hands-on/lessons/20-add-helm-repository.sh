#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 20: add and update a Helm repository"
require_context
explain "repo add records a chart catalog URL under the local name codecentric. repo update downloads the latest catalog index."
run helm repo add codecentric https://codecentric.github.io/helm-charts --force-update
run helm repo update
run helm repo list
