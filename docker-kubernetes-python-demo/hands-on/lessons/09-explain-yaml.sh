#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 09: use built-in API documentation"
require_context
explain "kubectl explain reads the cluster's API schema. Use it to learn legal YAML fields instead of guessing."
run kubectl explain deployment
run kubectl explain deployment.spec.replicas
run kubectl explain deployment.spec.template.spec.containers.resources
run kubectl explain service.spec.selector
explain "Now compare this output with config/deployment.yaml and config/service.yaml."
