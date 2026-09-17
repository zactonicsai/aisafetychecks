#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 21: search and inspect a Helm chart"
explain "search repo lists chart versions known in your local repository index."
run helm search repo codecentric/keycloakx --versions
explain "show chart displays chart metadata. show values displays every default setting; your values file overrides only selected settings."
run helm show chart codecentric/keycloakx --version 7.3.1
run helm show values codecentric/keycloakx --version 7.3.1
