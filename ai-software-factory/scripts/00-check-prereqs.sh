#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"

info "Required for the simulator"
need python3
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ is required"'
printf 'Python: %s\n' "$(python3 --version)"

info "Optional platform commands"
for tool in git docker podman kubectl kind helm kustomize ansible limactl tofu terraform aws az gcloud; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '  %-12s installed\n' "$tool"
  else
    printf '  %-12s not installed\n' "$tool"
  fi
done

info "The simulator can run now with ./scripts/10-local-up.sh"

