# Polyglot pipeline smoke tests

These deliberately tiny projects prove that a developer workspace or CI builder can compile and test each supported language. They are not production service templates.

Run every locally available toolchain:

```bash
../../scripts/21-test-examples.sh
```

| Directory | Command |
|---|---|
| `python` | `python3 -m unittest -v` |
| `go` | `go test ./...` |
| `rust` | `cargo test` |
| `cpp` | `cmake -S . -B build && cmake --build build && ctest --test-dir build` |
| `java` | `mvn test` |
| `web` | `npm install && npm test` |

Production templates should add locked dependencies, static analysis, coverage thresholds, SBOM/provenance, security tests, ownership, health checks, and container/Kubernetes definitions.

