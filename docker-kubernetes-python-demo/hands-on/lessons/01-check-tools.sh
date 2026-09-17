#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 01: check command-line tools"
explain "The shell searches PATH for each program. Version commands prove the client tools can start; they do not prove a cluster exists."
for tool in docker kubectl kind helm curl openssl; do
  printf '\nChecking %s...\n' "${tool}"
  need "${tool}"
  command -v "${tool}"
done
run docker --version
run kubectl version --client
run kind version
run helm version --short
