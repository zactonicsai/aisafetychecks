#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$HERE/00-check-prereqs.sh"
"$HERE/01-create-cluster.sh"
"$HERE/02-build-images.sh"
"$HERE/03-load-images.sh"
"$HERE/04-deploy-helm.sh"
"$HERE/05-test.sh"
echo "Done. Run scripts/06-port-forward.sh for browser/API access instructions."
