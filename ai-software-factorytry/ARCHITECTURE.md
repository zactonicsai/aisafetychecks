# Aether Forge Architecture

## 1. Goal and operating model

Build an **inner-source software factory** that:

- Gives every developer a **configured Linux workspace** (local Mac via container/VM, or remote CDE)
- Preinstalls language and test toolchains (Java, C/C++, Python, Go, Rust, web)
- Hosts a **package repo** so teams pull approved tools instead of the public internet
- Lets a developer **compose a custom pipeline** for their testing-tool or model project
- Builds, tests, stage-tests, and ships a **Linux image** (Docker or Podman)
- Deploys that image to local k3s, then Azure **AKS**, GCP **GKE**, or AWS **EKS**
- Shares knowledge across teams
- Tracks every change and supports **rollback**
- Uses **single sign-on** for every tool
- Stays **open source**, simple to operate, and easy to add access controls

Metaphor that must stay literal in the design:

| Factory term | Platform meaning |
|---|---|
| Floor | Control plane + portal (this simulation) |
| Stations | Git, packages, CI, model lab, registry, deploy |
| Workbench | Developer Linux workspace |
| Bill of materials | SBOM + lockfiles + ModelKit |
| Batch | A pipeline run |
| Shipping dock | Image registry + GitOps to Kubernetes |
| Foreman | Platform team + policy as code |

## 2. Design principles (keep it simple)

1. **One source of truth: Git.** Code, pipeline YAML, cluster desired state, workspace images, and docs live in Git. Rollback = revert + GitOps sync.
2. **Three portable contracts only.** Git repo, OCI image (and ModelKit), Kubernetes manifests. Do not invent a fourth.
3. **Identity first.** Keycloak OIDC is the only login. No local passwords on tools after bootstrap.
4. **Golden paths, not platforms-of-platforms.** One recommended stack. Swappable adapters at the edges.
5. **Policy at the gate, not in tribal knowledge.** Admission + CI checks, not wiki pages.
6. **Workspace is disposable.** Home/project volume persists; the image is rebuilt from Git.
7. **Least privilege + short-lived creds.** Workload identity on each cloud. No long-lived cloud keys in pipelines.
8. **Same pipeline locally and in the cloud.** `make test` and Tekton/Woodpecker steps call the same scripts.

### Design patterns used

| Pattern | Where |
|---|---|
| **Platform / paved road** | Factory floor exposes golden templates; teams fork them |
| **Sidecar / workspace image** | Toolchains baked into `forge-workbench` image |
| **Pipeline as code** | YAML in the app repo, reusable catalog of tasks |
| **GitOps** | Desired state in `gitops/` watched by Argo CD or Flux |
| **Strangler + adapters** | Cloud-specific modules behind a common interface |
| **Inner source** | Shared task library and test harnesses across teams |
| **Hexagonal ports** | “Deploy target” port: docker / podman / k3s / aks / gke / eks |
| **Package by capability** | Repos: `platform/`, `workspaces/`, `catalog/`, `apps/` |
| **RBAC + SSO federation** | Keycloak groups → Git, CI, K8s, registries |
| **Immutable artifacts** | Content-addressed images + model versions; promote, never mutate |
| **Canary + automatic rollback** | GitOps + health metrics; revert Git SHA |

Avoid: a different CI per language, per-cloud snowflake pipelines, storing models only on laptops, ClickOps clusters.

## 3. Layered architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  People & access                                                 │
│  Keycloak SSO (OIDC/SAML) + MFA  ·  groups  ·  SCIM optional     │
└────────────────────────────┬────────────────────────────────────┘
                             │ tokens
┌────────────────────────────▼────────────────────────────────────┐
│  Factory floor (control plane / portal)                          │
│  Catalog · workspaces · pipeline composer · promotions · audit   │
└──────┬────────────┬──────────────┬──────────────┬───────────────┘
       │            │              │              │
┌──────▼─────┐ ┌────▼─────┐ ┌──────▼─────┐ ┌──────▼──────────────┐
│ Source     │ │ Packages │ │ Knowledge  │ │ Observability       │
│ Forgejo    │ │ Nexus or │ │ Outline +  │ │ Prometheus Grafana  │
│ + DVC      │ │ Harbor   │ │ Mattermost │ │ Loki Tempo Falco    │
└──────┬─────┘ └────┬─────┘ └────────────┘ └─────────────────────┘
       │            │
┌──────▼────────────▼─────────────────────────────────────────────┐
│  Workbenches                                                     │
│  Mac: Colima/Podman/Lima VM  ·  Remote: Coder / DevSpace / k3s   │
│  Preinstalled compilers, testers, linters, browsers              │
└──────┬──────────────────────────────────────────────────────────┘
       │ git push
┌──────▼──────────────────────────────────────────────────────────┐
│  Build & test factory (Tekton or Woodpecker + reusable tasks)    │
│  build → unit → integration → model-eval / web-e2e → image scan  │
└──────┬──────────────────────────────────────────────────────────┘
       │ OCI + ModelKit
┌──────▼──────────────────────────────────────────────────────────┐
│  Registries                                                      │
│  Harbor (images, Helm, ModelKits) · MLflow · MinIO/DVC remote    │
└──────┬──────────────────────────────────────────────────────────┘
       │ GitOps
┌──────▼──────────────────────────────────────────────────────────┐
│  Runtime floors                                                  │
│  local k3s/kind  ·  Azure AKS  ·  GCP GKE  ·  AWS EKS            │
│  KServe / standard Deployments  ·  canary  ·  rollback           │
└─────────────────────────────────────────────────────────────────┘

Under the floor: OpenTofu + Ansible + thin cloud CLIs + signed images
```

## 4. Recommended open-source tool set (golden path)

Keep **one primary** per job. Alternatives are listed with tradeoffs.

### Identity and access

| Job | Primary (OSS) | Alternative | Notes |
|---|---|---|---|
| SSO / IdP | **Keycloak** | Authentik, Zitadel | OIDC to every tool. Groups: `platform`, `dev`, `ml`, `reviewer`, `read-only` |
| Secrets | **OpenBao** | Infisical, SOPS+age only | Terraform/Vault are BSL/BUSL — not OSI OSS. OpenBao is the Vault fork |
| Policy | **Open Policy Agent + Kyverno** | Gatekeeper | Kyverno is easier for K8s-shaped rules |

**Gotcha:** Keycloak is powerful and easy to misconfigure. Start with two realms max (`internal`, `ci-bots`). Never let tools keep their own user databases after cutover.

### Source, review, knowledge

| Job | Primary | Alternative |
|---|---|---|
| Git + PRs | **Forgejo** | GitLab CE (heavier), Gitea |
| Large data/models in Git flow | **DVC** + MinIO | Git LFS (hits size walls) |
| Docs / runbooks | **Outline** or Grav | Wiki.js |
| Team chat | **Mattermost** | Zulip |
| Architecture decision records | Markdown in `docs/adr/` | — |

**Gotcha:** Do not use GitHub.com as the system of record if the requirement is “we operate the factory.” Mirror is fine.

### Package and artifact repositories

| Job | Primary | Alternative |
|---|---|---|
| Language packages (PyPI, Maven, npm, crates, Go proxy, apt) | **Nexus OSS** or **JFrog-less** mix | **Google Artifact Registry** is not OSS; **Nexus** or **Harbor + Pulp** |
| Container / OCI / Helm / ModelKit | **Harbor** | Zot (lighter) |
| Generic blobs | **MinIO** | SeaweedFS |
| AI project pack | **KitOps ModelKit** on Harbor | MLflow artifacts only |

Recommended split: **Harbor for OCI**, **Nexus for language/apt**, **MinIO for DVC/MLflow artifacts**. That is two extra boxes — worth it. One Nexus-for-everything is simpler but weaker for container CVE scanning.

**Gotcha:** Developers will bypass the proxy the first day if `pip`/`npm` are not preconfigured in the workspace image. Bake registry URLs into the workbench.

### Workspaces (the “Linux configure VM”)

| Job | Primary | Alternative |
|---|---|---|
| Local on Mac | **Colima** or **Podman Machine** + `forge-workbench` image | Lima, UTM full VM, Nix + direnv only |
| Remote CDE | **Coder** (OSS) on k3s/K8s | DevSpace, Gitpod self-hosted, Eclipse Che |
| Strong isolation | Kata / Firecracker microVMs | Plain containers (weaker) |
| Host config (rare bare metal) | **Ansible** | NixOS (steeper) |

Workbench image contains:

- Compilers: JDK 21, gcc/clang, Python 3.12, Go, Rust stable
- Build: Maven/Gradle, CMake/Ninja, pip/uv, cargo, go
- Test: JUnit/TestNG, GoogleTest, pytest, gotest, cargo test, Playwright/Cypress, k6, Testcontainers
- AI: uv, jupyterlab, MLflow CLI, DVC, kit CLI
- Containers: Docker *or* Podman + buildah + kind/k3d
- Quality: ruff, clang-tidy, spotbugs, golangci-lint, clippy
- Supply chain: syft, grype, cosign

**Mac gotchas:**

- Docker Desktop licensing may not be acceptable — prefer **Colima** or **Podman Desktop**
- Volume performance on virtiofs vs osxfs: put heavy builds on a Linux VM disk, not a bind-mounted macOS directory
- Apple Silicon: multi-arch (`linux/amd64` + `linux/arm64`) images or you will surprise EKS/GKE/AKS amd64 nodes
- Nested Kubernetes on Mac is fine for *compose*, not for load tests

### CI / custom pipeline factory

| Job | Primary | Alternative | When |
|---|---|---|---|
| Kubernetes-native pipelines | **Tekton** + Tekton Dashboard / Pipelines-as-Code | Argo Workflows | You already run K8s for CI |
| Lightweight CI | **Woodpecker** | Gitea Actions | Small teams, simple YAML |
| Reusable tasks | Tekton ClusterTasks / Woodpecker plugins | Jenkins shared libs | Avoid Jenkins unless you already own it |

Pipeline stages (fixed contract, custom steps inside):

1. `fetch` — git + DVC pull
2. `build` — language matrix
3. `unit`
4. `integration` / `contract`
5. `eval` — model metrics vs baseline, or Playwright against staging
6. `package` — OCI image + SBOM + (optional) ModelKit
7. `scan` — grype + policy
8. `publish` — Harbor
9. `stage` — deploy to `ns-stage` via GitOps PR
10. `promote` — same image digest to `ns-prod`
11. `rollback` — previous Git SHA / previous digest

Developers do **not** write cloud-specific YAML. They pick tasks from the catalog and set parameters.

**Gotcha:** Letting every team invent YAML from scratch recreates the snowflake problem. Ship **pipeline templates** (`lang-python-ml`, `lang-java-svc`, `lang-cpp-lib`, `lang-go-api`, `lang-rust-cli`, `web-frontend`, `custom-test-tool`).

### ML / AI specific

| Job | Primary | Alternative |
|---|---|---|
| Experiment tracking + registry | **MLflow** | Aim, Weight & Biases (not OSS core) |
| Data/model versioning | **DVC** | LakeFS |
| Feature store (only if needed) | **Feast** | Skip until two+ models share features |
| Serving | **KServe** | BentoML + vanilla Deployment |
| Orchestration on K8s | **Argo Workflows** or Tekton | Kubeflow (heavy) |
| Eval harness | pytest + custom metrics + Promptfoo (OSS) | — |

**Gotcha:** Kubeflow is a platform, not a library. Most teams only needed notebooks + pipelines + serving. Start with Jupyter on Coder + Tekton + MLflow + KServe.

### Deploy / GitOps / IaC

| Job | Primary | Why not the other |
|---|---|---|
| IaC | **OpenTofu** | Terraform is BUSL (IBM). OpenTofu is MPL OSS |
| Config management | **Ansible** | For image hardening and rare VMs, not for K8s apps |
| Cluster apps | **Helm + Kustomize (pick one overlay style)** | Running both without rules duplicates replica counts |
| GitOps | **Argo CD** *or* **Flux** | Argo = UI; Flux = smaller, Git-only. Pick one |
| Multi-cloud control | OpenTofu modules + optional **Crossplane** | Don’t start with Crossplane |
| Image sign/verify | **cosign** + Kyverno verify | Unsigned images must not schedule |

Cloud CLIs (not platforms — just actuators):

- `aws`, `az`, `gcloud`, `kubectl`, `helm`, `tofu`, `ansible-playbook`

**Correction:** “Azure EKS” is not a product. Use **Azure AKS**, **Amazon EKS**, **Google GKE**.

### Observability and audit

Prometheus, Grafana, Loki, Tempo, OpenTelemetry collector, Falco. Audit log from Keycloak + Forgejo + Harbor + Kubernetes API shipped to Loki.

## 5. Target options — pros, cons, gotchas

### 5.1 Local Mac testing

| Option | Pros | Cons | Gotchas |
|---|---|---|---|
| Colima + workbench container | Fast, OSS-friendly, matches Linux CI | Not a full VM | File sharing slowness; start Colima with more CPU/RAM |
| Podman Machine | Daemonless mental model matches prod rootless | Slightly less Docker-compose muscle memory | `docker` alias confusion |
| Lima / UTM full Ubuntu VM | Closest to “Linux configure VM” | Heavier | Keep the VM golden via Ansible; don’t snowflake it |
| Nix + direnv on Mac | Reproducible shells | Does not replace Linux images | Still build linux/amd64 in CI |
| kind / k3d / minikube | Real K8s API locally | Not prod networking or IAM | Never tune prod manifests only against kind |

**Best practice:** Mac is an editor + thin VM. The workbench **is Linux**. CI is the same Linux.

### 5.2 Docker / Podman images

| Option | Pros | Cons | Gotchas |
|---|---|---|---|
| Docker | Ubiquitous | Desktop license; daemon | Don’t require Docker.sock in every workspace |
| Podman + buildah | Rootless, OSS | Some Compose gaps | Generate the same OCI index |
| Multi-stage + distroless | Small attack surface | Harder debug | Ship a `-debug` tag separately |

Always: SBOM (syft), scan (grype), sign (cosign), pin digest on deploy.

### 5.3 Kubernetes substrates

| | Local k3s/k3d | Azure AKS | GCP GKE | AWS EKS |
|---|---|---|---|---|
| Role | Dev/stage-like | Enterprise / Entra shops | Most managed / AI-friendly | Deepest ecosystem |
| Control plane cost | Free | Free tier available | Free / cheap Autopilot | ~$73/mo per cluster |
| Identity | Keycloak OIDC | Entra + Workload ID | Workload Identity Fed | IRSA / Pod Identity |
| GPU | Optional | NC/ND | GPU + TPU | P4/P5 etc. |
| GitOps addon | You install | Flux extension | Config Sync | Flux addon |
| Pros | Same API, cheap | Entra, Windows nodes, cheap entry | Autopilot, upgrades, AI | IAM, Karpenter, ecosystem |
| Cons | Not IAM/GPU-real | Azure-shaped networking | GCP lock-in temptation | You assemble more; paid CP |
| Gotchas | Default Traefik vs prod ingress | “EKS” name mix-up; CNI IP exhaustion | Autopilot rejects some privileged pods | VPC CNI IP exhaustion; IRSA misconfig |

**Multi-cloud rule:** the factory never deploys with `aws eks update-kubeconfig && kubectl apply` as the source of truth. OpenTofu creates the cluster; Argo/Flux applies apps from Git. Cloud modules differ; app manifests do not.

### 5.4 IaC and config

| Tool | Pros | Cons | Gotchas |
|---|---|---|---|
| OpenTofu | OSS, Terraform-compatible | Some brand-new TF providers lag | Pin provider + module versions |
| Ansible | Idempotent VM/image config | Not for app deploy on K8s | Don’t Ansible-mutate running clusters |
| Shell + CLIs | Good glue | Unreviewed bash becomes production | Every script `set -euo pipefail`; wrap in OpenTofu null_resource only when unavoidable |
| Crossplane | K8s API for clouds | Cognitive load | Year-two tool, not day-one |

## 6. Access model (simple)

Keycloak groups map everywhere the same way:

| Group | Git | Pipeline | Registry | Cluster | Floor admin |
|---|---|---|---|---|---|
| platform | admin | admin | admin | cluster-admin (break-glass) | yes |
| ml-engineer | write team repos | run + promote stage | push models | ns-stage deploy | no |
| developer | write team repos | run CI | push app images | ns-dev | no |
| reviewer | read + approve | no prod promote | pull | read | no |
| read-only | read | read logs | pull | read | no |

Promotion to production = **two-person rule**: pipeline produces an immutable digest; a reviewer approves a GitOps PR.

SSO integration list (OIDC): Forgejo, Harbor, Nexus, Coder, Woodpecker/Tekton Dashboard, Argo CD, Grafana, MLflow (via oauth proxy), Outline, Mattermost, K8s apiserver OIDC.

**Gotcha:** Kubernetes OIDC + cloud IAM are *different*. Users log into kubectl via OIDC; **pods** use workload identity. Mixing them is a common outage.

## 7. End-to-end flow

```
Developer laptop (Mac)
    │  colima start && forge ws start my-project
    ▼
Linux workbench (container or Coder workspace)
    │  tools already on PATH; extra debs from Nexus apt
    │  code + tests + optional custom test harness
    │  git commit && git push origin feat/…
    ▼
Forgejo  →  PR checks (lint, unit)
    │  merge to main
    ▼
Pipeline factory (template + extra tasks the team added)
    build → test → eval → image → sbom/scan/sign → Harbor
    ▼
GitOps repo updated with new digest (automated PR)
    ▼
Argo CD / Flux
    ns-dev → ns-stage (smoke + model eval gate) → ns-prod
    ▼
If SLO burn: sync previous Git SHA (rollback). Image never overwritten.
```

Custom testing-tool development uses the same path. The “unique testing tool” is just another repo from template `custom-test-tool`, published as an image and optionally as a Tekton task so other teams can add it to their pipeline.

## 8. Repository layout (platform monorepo + app repos)

```
platform/
  tofu/                 # clusters, networks, IAM bindings
    modules/k8s-cluster # abstracts AKS/GKE/EKS
    modules/identity
    envs/dev-local
    envs/azure-aks
    envs/gcp-gke
    envs/aws-eks
  ansible/              # harden workbench AMIs / golden VMs
  images/workbench/     # Containerfile for developer VM-equivalent
  catalog/              # Tekton tasks, pipeline templates
  gitops/               # root apps per cluster
  policies/             # Kyverno, OPA
  scripts/              # thin CLI wrappers

apps live in separate Forgejo repos created from templates
```

## 9. What not to do

- Do not run three different CI systems “because Java likes Jenkins.”
- Do not give developers cloud console Admin so they can “just try AKS.”
- Do not mutate images (`latest` in production).
- Do not store model weights only in Slack.
- Do not make the portal a second source of truth — it only *drives Git*.
- Do not install the entire Kubeflow umbrella on day one.
- Do not treat Terraform Cloud / Vault Enterprise as OSS.

## 10. Minimal viable factory (order of build)

1. Keycloak + Forgejo + Harbor + MinIO
2. Workbench image + Colima instructions + Coder optional
3. One pipeline template (Python) + Woodpecker or Tekton
4. Local k3s + Argo CD
5. MLflow + DVC
6. OpenTofu module for *one* cloud (the one you actually have)
7. Kyverno + cosign verify
8. Outline + Mattermost
9. Second and third clouds only when a real workload needs them

The simulation in `simulation/` pretends all of the above exist so teams can learn the floor before the steel is erected.
