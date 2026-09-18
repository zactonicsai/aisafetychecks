#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
need python3
cd "$ROOT_DIR"
info "Starting the simulator at http://127.0.0.1:${FACTORY_PORT:-8080}"
exec python3 -m app.server --host 127.0.0.1 --port "${FACTORY_PORT:-8080}"

