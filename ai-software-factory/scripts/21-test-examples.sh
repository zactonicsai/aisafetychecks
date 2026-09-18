#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
cd "$ROOT_DIR/examples/polyglot"

if command -v python3 >/dev/null 2>&1; then (cd python && python3 -m unittest -v); else warn "Skipping Python"; fi
if command -v go >/dev/null 2>&1; then (cd go && go test ./...); else warn "Skipping Go"; fi
if command -v cargo >/dev/null 2>&1; then (cd rust && cargo test); else warn "Skipping Rust"; fi
if command -v cmake >/dev/null 2>&1; then (cmake -S cpp -B cpp/build && cmake --build cpp/build && ctest --test-dir cpp/build); else warn "Skipping C++"; fi
if command -v mvn >/dev/null 2>&1; then (cd java && mvn -q test); else warn "Skipping Java"; fi
if command -v npm >/dev/null 2>&1; then (cd web && npm install && npm test); else warn "Skipping web"; fi

