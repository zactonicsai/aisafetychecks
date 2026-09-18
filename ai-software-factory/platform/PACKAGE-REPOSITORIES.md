# Trusted package repository design

The package repository is the factory tool crib. Developers and CI pull from controlled proxy endpoints instead of downloading arbitrary dependencies directly from the internet.

## Repository pattern

For each ecosystem, create three logical repositories:

1. `*-proxy`: approved upstream proxy/cache.
2. `*-hosted`: internally produced packages.
3. `*-group`: one endpoint combining hosted packages and approved proxies.

Examples: `maven-group`, `npm-group`, `pypi-group`, `nuget-group`, `cargo-group`, `go-proxy`, `apt-group`, and `oci-project`.

## Client configuration examples

Use placeholders and short-lived credentials delivered at login or job runtime. Do not commit tokens.

### Python

```bash
python -m pip config set global.index-url https://packages.example.invalid/repository/pypi-group/simple
python -m pip config set global.require-virtualenv true
```

### npm/pnpm

```bash
npm config set registry https://packages.example.invalid/repository/npm-group/
```

### Maven

Configure a mirror in user or CI-generated `settings.xml`:

```xml
<mirror>
  <id>factory-maven</id>
  <mirrorOf>*</mirrorOf>
  <url>https://packages.example.invalid/repository/maven-group/</url>
</mirror>
```

### Go

```bash
go env -w GOPROXY=https://packages.example.invalid/repository/go-proxy,direct
go env -w GOSUMDB=sum.golang.org
```

For a restricted network, mirror the checksum database or set the approved internal equivalent instead of silently disabling verification.

### Cargo

Use source replacement in `.cargo/config.toml` and preserve lockfiles. Confirm that the chosen repository actually supports Cargo's sparse index; repository products vary.

### Containers

Mirror approved base images into Harbor and refer to them by digest:

```dockerfile
FROM harbor.example.invalid/base/python@sha256:REPLACE_WITH_APPROVED_DIGEST
```

## Controls

- Allowlist upstream repositories and block direct egress from CI after bootstrap.
- Preserve lockfiles and verify checksums/signatures.
- Quarantine newly requested packages when risk requires review.
- Detect dependency confusion by reserving internal names and preferring hosted packages.
- Generate SBOMs and scan licenses/vulnerabilities before promotion.
- Record exceptions with owner, reason, scope, and expiration.
- Keep vulnerability databases mirrored and timestamped for air-gapped builds.
- Retain exact release dependencies for the supported lifetime of the product.

## Gotchas

- A cache is not a permanent archive unless retention policy says it is.
- Different ecosystems have different metadata and signature behavior.
- Repository editions may support formats differently; validate the exact open-source edition.
- Package credentials in URLs, command history, logs, or lockfiles are leaks.
- Deleting a compromised package from the proxy does not remove it from developer caches or old images.

