# Platform installation strategy

Do not install the entire catalog on every laptop. The simulator and `kind` overlay are the local learning path; shared factory services belong in a non-production platform cluster and should be added in this order.

## Layer 1 — identity and source

1. PostgreSQL with tested backups.
2. Keycloak connected to the authoritative directory and MFA.
3. Gitea/Forgejo with OIDC, protected branches, owners, webhooks, and audit export.
4. A package proxy following [PACKAGE-REPOSITORIES.md](PACKAGE-REPOSITORIES.md).

## Layer 2 — delivery

1. Harbor registry with OIDC, immutable release tags, retention, vulnerability feeds, replication, and object-storage backup.
2. Tekton Pipelines/Triggers with ephemeral, unprivileged task pods and separate service accounts for pull-request and release trust zones.
3. Argo CD with Keycloak OIDC, repository credentials from a secret manager, AppProjects that limit source repositories/namespaces, and admin disabled after bootstrap.
4. Kyverno in audit mode first, then enforce non-root, approved registries, immutable digests, and signature verification.

## Layer 3 — models and evidence

1. MinIO or cloud object storage with versioning, encryption, lifecycle, and replication.
2. PostgreSQL-backed MLflow using object storage for artifacts.
3. Project-owned evaluation suites and model cards.
4. OpenTelemetry, Prometheus, Grafana, Loki, and Tempo with retention/cardinality budgets.

## Layer 4 — optional scale features

- Backstage when the number of components makes catalog/search/template automation valuable.
- JupyterHub for governed shared notebooks.
- KServe for standardized model inference and autoscaling.
- Argo Rollouts for canary/blue-green promotion.
- Kubeflow only when multiple teams need its training operators, pipelines, and notebook integrations enough to justify the operational weight.

## Installation rule

Treat every platform tool as a product:

- Pin the upstream release and chart/manifests.
- Mirror images and charts into approved internal repositories.
- Keep values/configuration in a platform Git repository.
- Scan and sign the mirrored images.
- Integrate Keycloak groups before onboarding users.
- Define owner, SLO, backup, restore, patch, upgrade, and removal procedures.
- Test upgrades in a disposable cluster with restored data.

Use official upstream delivery mechanisms where possible. Tekton publishes versioned manifests; Argo CD, Harbor, and Gitea publish Helm charts; Keycloak provides an Operator. Avoid a single shell script that installs “latest” from the internet because it is neither repeatable nor appropriate for an air-gapped or controlled environment.

## Minimum production separation

| Boundary | Recommendation |
|---|---|
| Platform control plane | Dedicated cluster or strongly isolated platform namespaces and nodes |
| Development/test | Separate account/subscription/project from production |
| Production | Separate cluster and cloud boundary with restricted GitOps credentials |
| CI pull requests | Untrusted, ephemeral workers with no release or production secret access |
| CI releases | Protected branch/tag only, isolated service account, signed outputs |
| Stateful data | Managed databases/object storage where practical; tested backups outside the cluster |

