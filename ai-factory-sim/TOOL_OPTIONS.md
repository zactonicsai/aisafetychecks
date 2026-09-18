# Tool options, pros, cons and gotchas

Generated from `catalog.py` by `python3 factory_sim.py run`. Edit the catalogue, not this file.

Scope: CPU only, small models, no GPUs. Every default pick is open source.

## Sign-in and access

One login for every tool. Groups decide who can do what.

**Default pick:** Keycloak (Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Keycloak | Mature OIDC and SAML, fine-grained groups, large community. | Heaviest to run. Major upgrades arrive often and need care. |
| Authentik | Friendlier admin UI. Built-in proxy for apps that have no SSO. | Smaller ecosystem. Some features are enterprise-only. |
| Dex or Authelia | Tiny footprint. | No real user management: you still need a directory behind them. |

**Gotchas**

- If the identity provider is down, nobody can log in anywhere. Run two replicas, back up its database, and keep one sealed break-glass admin account in each tool.
- Disabling a user does not revoke their SSH keys, personal tokens or robot accounts inside each tool. Offboarding must be a script that visits every tool.
- Many open-core tools charge for SSO or group sync. Check the free edition before adopting a tool.
- Keep the realm as code (keycloak-config-cli or the OpenTofu provider) so access changes are reviewed pull requests.

## Code, reviews and packages

Git hosting, pull requests, and the package registries for every language.

**Default pick:** Forgejo (GPL-3.0-or-later)

| Option | Pros | Cons |
|---|---|---|
| Forgejo (or Gitea) | One small binary. Built-in registries for Maven, PyPI, Cargo, Go, Conan, npm, containers and Helm. OIDC login. | Fewer enterprise controls. Smaller plugin ecosystem. |
| GitLab CE | Code, CI, registry and issues in one product. Very mature CI. | Wants 8 GB RAM or more. Many approval and access features sit in paid tiers. |

**Gotchas**

- Protect main on day one: one review from someone else plus green CI.
- Git is the source of truth for deployments too, so mirror and back up the forge nightly.
- Datasets and model files do not belong in Git. Use DVC and object storage.
- Forgejo Actions reads GitHub-style workflows, but not every marketplace action works. Keep workflows thin.

## CI runners

Runs the same make targets a developer runs on a Mac, on every push.

**Default pick:** Forgejo Actions or Woodpecker CI (GPL-3.0 / Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Forgejo Actions or Woodpecker | Simple, container-native, little to operate. | Fewer features than the big engines. |
| Jenkins | Does anything. A plugin exists for everything. | Plugin and security upkeep never ends. Groovy pipelines get hard to read. |
| Tekton or Argo Workflows | Kubernetes-native. Good for training jobs shaped like graphs. | Verbose YAML and a steep learning curve. |
| Dagger | Pipelines as code that run the same on a Mac and in CI. | One more engine to learn and host. |

**Gotchas**

- Keep pipeline YAML thin. Logic lives in the Makefile so a Mac and CI run the same commands.
- Pin actions and images by commit SHA or digest, scanners included. In March 2026 hijacked Trivy action tags stole CI secrets and led to poisoned LiteLLM releases on PyPI.
- A runner with the Docker socket mounted is root on its host. Use rootless BuildKit or throwaway runners.
- Proxy and cache dependencies through your own registry, or builds crawl and break when the internet hiccups.
- Latency tests are flaky on shared runners. Give speed gates a dedicated runner with fixed CPU.

## Images, packages and signatures

Stores what CI builds, scans it, signs it, and copies it next to each cluster.

**Default pick:** Harbor plus the forge's package registries (Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Harbor | Scanning, signing policy, OIDC, and replication to ACR, Artifact Registry and ECR. | Several services plus Postgres and Redis to run. |
| Forge built-in registry only | No extra tool. | No scanning, admission policy or replication. |
| Zot | Tiny OCI-native registry. | Fewer features and a smaller community. |
| Cloud registries alone | Managed and close to the clusters. | Three places to manage, and not open source. |

**Gotchas**

- Pulling images across clouds costs money and time. Replicate to the registry beside each cluster.
- Deploy by digest, never by tag. A tag can move; a digest cannot.
- Harbor's login mode cannot be switched once users exist. Choose OIDC at install.
- Set retention and garbage collection early or the disk fills.

## Supply-chain checks

Finds leaked secrets, risky code and vulnerable dependencies before anything ships.

**Default pick:** Gitleaks, Opengrep, Syft + Grype or Trivy, cosign, Kyverno, ZAP (MIT / LGPL / Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Trivy | One tool for images, IaC, SBOMs and secrets. | Its releases and actions were compromised in March 2026. Pin exact versions and digests. |
| Syft + Grype | Clean split: build the SBOM once, scan it many times. | Two tools instead of one. |
| SonarQube Community Build | Quality gates for many languages in one UI. | Branch and pull-request analysis is paid. |

**Gotchas**

- Scanners are software too. Pin them and verify them like any other dependency.
- Block criticals that have a fix. Blocking everything stops the line daily and teaches people to bypass it.
- Keep the ignore list in Git with an expiry date on every entry.
- Signing without verifying is theatre. Enforce signatures at admission with Kyverno.

## Data and object storage

Versions datasets so any model can be traced to the exact data that trained and tested it.

**Default pick:** DVC on each cloud's bucket (S3, GCS, Azure Blob) (Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| DVC | Feels like Git. No server. Works with any bucket. | No UI. Slow with millions of tiny files. |
| lakeFS | Branch and merge for whole data lakes, with a UI. | Another service to run. |
| Git LFS | Simplest possible. | Poor at scale, and fills the forge's disk. |

**Gotchas**

- MinIO's community edition is no longer maintained (repository archived April 2026). For self-hosted S3 use SeaweedFS, Garage or Ceph RGW.
- Record the dataset hash in every training run. Without it lineage is a guess.
- Golden test sets must be held out and access-controlled, or they leak into training.

## Experiments and model registry

Remembers every training run and which model version is the champion.

**Default pick:** MLflow (Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| MLflow | The de facto standard. Tracking, registry and evaluation for any framework. | No OIDC in the open-source server. Plain UI. |
| ClearML | Tracking plus orchestration and data management. | Heavier server, some open-core parts. |
| Aim | Fast, pleasant run comparison. | No model registry. |

**Gotchas**

- Put oauth2-proxy in front of MLflow to get SSO.
- Use aliases (champion, candidate). Stages are deprecated.
- Pin the model version in Git for each deployment. Do not resolve an alias at runtime, or rollbacks stop being auditable.
- Back up both halves: metadata in Postgres and artifacts in the bucket.

## Model testing

Decides with numbers, not opinions, whether a model may move down the line.

**Default pick:** pytest golden sets, lm-evaluation-harness or Inspect, Fairlearn, Evidently, garak, k6 (MIT / Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| pytest plus your own golden sets | Everyone knows it. Runs the same on a Mac and in CI. | You build the metrics and reports yourself. |
| lm-evaluation-harness or Inspect AI | Standard benchmarks and agent-style evaluations. | Slow on CPU: run a small subset per commit and the full set nightly. |
| promptfoo or DeepEval | Quick prompt and RAG regression tests. | Judge-model costs. promptfoo stays MIT but has belonged to OpenAI since March 2026. |
| garak or PyRIT | Red-team probes: jailbreaks, prompt injection, data leakage. | Noisy results that need triage. |

**Gotchas**

- Models are not deterministic. Fix seeds and thread counts, and assert within a tolerance band, never equality.
- Test the file you ship. Quantizing to int8 shifts accuracy, so gate the ONNX or GGUF artifact, not the training checkpoint.
- On a Mac force device='cpu', or PyTorch may quietly use MPS and give different numbers from the cloud.
- Thresholds live in Git and change by pull request.
- Two tiers: a smoke suite under two minutes on every commit, the full suite on every candidate.

## Model serving on CPU

Turns a model file into an HTTP service that is fast enough on ordinary CPUs.

**Default pick:** ONNX Runtime or llama.cpp in a plain container (MIT)

| Option | Pros | Cons |
|---|---|---|
| Plain container (FastAPI + ONNX Runtime) | Simplest. Runs the same on Docker, kind and every cloud. | You write the batching and health checks. |
| BentoML | Python-first packaging with batching built in. | Another abstraction to learn. |
| KServe | Canary, scale to zero, standard inference protocol. | More moving parts than small CPU models need. |

**Gotchas**

- Seldon Core moved to a BSL licence in 2024 and is no longer open source.
- Kubernetes CPU limits throttle and wreck p95 latency. Set requests equal to limits and match OMP_NUM_THREADS to the request.
- Chips differ per cloud (AVX-512 or AMX on x86, NEON on arm64). Measure latency on each cloud, not once.
- Small models can ship inside the image, so one digest rolls back code and model together.

## Infrastructure as code

Creates the clusters, networks, buckets and identities on each cloud.

**Default pick:** OpenTofu (MPL-2.0)

| Option | Pros | Cons |
|---|---|---|
| OpenTofu | Open source. Drop-in for Terraform code and providers. State encryption built in. | The very newest Terraform features can differ. |
| Terraform | Largest ecosystem and documentation. | BSL licence, so not open source. |
| Pulumi | Real programming languages. | A different model plus a state service. |
| Crossplane | Kubernetes-native control plane. | Steep, and needs a cluster before it can build one. |

**Gotchas**

- Remote state with locking, one state per cloud per environment. Never local state.
- OpenTofu builds the cluster and installs Argo CD, then stops. Do not manage in-cluster apps with it.
- There is no real rollback: you revert and apply. Guard stateful resources with prevent_destroy and backups.
- Pin provider versions and commit the lock file.
- Keep Kubernetes minor versions aligned across AKS, GKE and EKS.

## Machines, scripts and cloud CLIs

Sets up Macs, runners and the Docker host, and hides three cloud CLIs behind one command.

**Default pick:** Ansible, shell, and az / gcloud / aws behind factoryctl (GPL-3.0)

| Option | Pros | Cons |
|---|---|---|
| Ansible | Agentless and readable. Good for Macs, runners and VMs. | Slow across many hosts. Logic in YAML gets ugly. |
| Shell scripts | No dependencies. | Hard to keep idempotent. Use set -euo pipefail and shellcheck. |
| Packer images | Immutable and fast to boot. | Every change means a rebuild. |

**Gotchas**

- Ansible is not for deploying apps to Kubernetes. That is GitOps' job.
- kubectl login differs per cloud: AKS needs kubelogin, GKE needs gke-gcloud-auth-plugin, EKS uses aws eks get-token. Wrap all three.
- Pin CLI versions with a Brewfile and mise so every Mac and runner matches.

## GitOps and safe rollout

Makes each cluster match what Git says, and rolls back when numbers go bad.

**Default pick:** Argo CD and Argo Rollouts, Helm + Kustomize (Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Argo CD | Clear UI, SSO, roles by group. | A central hub needs network paths and credentials into every cluster. |
| Flux | Pull-only and light. No inbound access needed. | Minimal UI. |
| helm upgrade from CI | Simplest. | No drift detection, and CI holds cluster credentials. |

**Gotchas**

- With auto-sync on, 'argocd app rollback' is refused. Roll back with git revert.
- One Argo CD per cluster, pulling from Git, avoids a hub that holds the keys to every cloud.
- ingress-nginx was retired in March 2026. Use a Gateway API implementation such as Envoy Gateway, Traefik or Cilium.
- Bitnami stopped publishing free versioned images and charts in August 2025. Use upstream charts and operators such as CloudNativePG.

## Secrets

Keeps passwords and keys out of Git and out of CI variables.

**Default pick:** External Secrets Operator with each cloud's secret manager; SOPS + age for Git (Apache-2.0 / MPL-2.0)

| Option | Pros | Cons |
|---|---|---|
| External Secrets + cloud secret managers | No vault to run. Uses workload identity. | Three backends to understand. |
| SOPS + age | Encrypted secrets in Git. Very simple. | You distribute keys by hand. No rotation or audit trail. |
| OpenBao | Open-source fork of Vault: dynamic secrets and auditing. | One more highly-available service. |

**Gotchas**

- CI reaches each cloud through workload identity. Store no long-lived cloud keys.
- Workload identity comes in three flavours (AKS Workload Identity, GKE Workload Identity Federation, EKS Pod Identity). Hide them behind module outputs.
- HashiCorp Vault is BSL-licensed. OpenBao is the open-source line.

## Metrics, logs and drift

Shows whether services and models are healthy, and wakes someone when they are not.

**Default pick:** Prometheus, Grafana, Loki, OpenTelemetry, Evidently (Apache-2.0 / AGPL-3.0)

| Option | Pros | Cons |
|---|---|---|
| Prometheus + Grafana + Loki | The standard. Dashboards exist for everything. | Grafana and Loki are AGPL: fine to use, relevant if you modify and resell. |
| VictoriaMetrics | Lighter, with cheaper long-term storage. | Smaller community. |
| SigNoz | Metrics, logs and traces in one product. | Younger project. |

**Gotchas**

- Grafana OSS maps roles from OIDC claims, but team sync is an enterprise feature.
- Run one metrics stack per cluster and remote-write to the hub. Never scrape across clouds.
- Model quality and drift are production metrics. Alert on them exactly like error rates.

## Portal, docs and chat

Lets one team find, understand and reuse what another team built.

**Default pick:** A static portal first, MkDocs + ADRs in Git, Zulip (Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Static portal (like this one) | Hours to set up and nothing to patch. | No templates or scorecards engine. |
| Backstage | Catalog, templates, docs and plugins. | It is a framework you build and upgrade, so it needs a TypeScript owner. Worth it past roughly 50 services. |
| Wiki.js or BookStack | Friendly editing for everyone. | Docs drift away from the code. |

**Gotchas**

- Mattermost's free edition has no generic OIDC login. Zulip does.
- Keep docs beside the code, or they rot.
- Put an owner file in every repo from day one.

## Local development on macOS

Gives every developer the same tools and a small copy of the platform on a laptop.

**Default pick:** Brewfile, mise, Colima, kind, devcontainers, pre-commit (MIT / Apache-2.0)

| Option | Pros | Cons |
|---|---|---|
| Colima | Free, light, command-line. | No GUI. |
| Podman Desktop or Rancher Desktop | GUI, with Kubernetes built in. | Occasional compatibility quirks. |
| Docker Desktop | Smoothest experience. | Paid licence for larger companies, and not open source. |

**Gotchas**

- Apple Silicon is arm64 and most cloud nodes are amd64. Build multi-arch images; emulating amd64 on a Mac is slow.
- arm64 cloud nodes (Graviton, Cobalt, Axion) match the Mac and cost less. Worth a staging pool.
- kind is not a cloud: no real load balancers, storage classes or IAM. Staging on real clusters stays mandatory.
