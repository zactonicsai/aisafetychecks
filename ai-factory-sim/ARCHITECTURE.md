# AI model testing software factory: architecture

A software factory is a shared assembly line for software. Developers put code and data in at one end. Tested, signed, deployable services and models come out the other end, and every step in between is automatic, recorded and reversible.

This one is built for teams that build and test **small AI models on CPUs** (no GPUs), in Java, C/C++, Python, Go, Rust and web code. It runs locally on a Mac, in Docker, and on Kubernetes in Azure (AKS), Google Cloud (GKE) and AWS (EKS). Every tool is open source. Facts were checked in September 2026.

Pros, cons and gotchas for every tool are in `TOOL_OPTIONS.md`, which is generated from `catalog.py`.

---

## 1. Try it first: a five-minute walkthrough

The simulator plays one week on the factory floor so you can see every tool type working together before you install anything.

1. Open Terminal on your Mac and go to this folder.
2. Run `python3 factory_sim.py run`. It needs nothing but the Python that ships with macOS.
3. Watch the event log scroll past. Each line is one tool doing one thing: who, what, result.
4. Open `site/index.html` in a browser.
5. Click station 5, **Evaluate**. Version v3 has a red cell: the fairness gate stopped it.
6. Click station 7, **Deploy**. Version v2 passed every offline test, then failed its production canary and was reverted automatically in about five minutes.
7. Change the **Signed in as** menu to `kai` (a viewer) and press **Roll back production**. It is refused, and the message says which permission is missing.

That is the whole idea in miniature: one sign-in, one line, gates with numbers, rollback by Git.

---

## 2. The big picture

```
  Developer Mac                      Keycloak (single sign-on)
  Brewfile, kind                     groups -> roles in every tool
       |                                        :
       | git push                               :
       v                                        v
  +---------+     +------------+     +---------------------+
  | Forgejo | --> | CI runners | --> | Harbor              |
  | code,   |     | make lint  |     | SBOM, scan, sign    |
  | reviews,|     | test build |     +---------------------+
  | packages|     +------------+                |
  +---------+           |                       |
                        v                       |
                +---------------+               |
                | DVC + MLflow  |               |
                | data, runs,   |               |
                | registry      |               |
                +---------------+               |
                        |                       |
                        v                       v
                +----------------------------------+
                | eval gates  ->  environments repo |
                | (limits in Git)  (desired state)  |
                +----------------------------------+
                        | pulled by Argo CD in each place
      +-----------+-----+------+---------+---------+
      v           v            v         v         v
   mac-kind   docker-dev      AKS       GKE       EKS
                               \         |         /
                         Prometheus, Grafana, Loki, drift
                                         |
                          bad numbers -> automatic rollback
```

**Shape: a hub and spokes.** One small hub cluster runs the shared tools (sign-in, code, CI, registry, MLflow, portal). Workloads run on the spokes: a laptop, a Docker host, and staging plus production clusters in three clouds. Only a thin OpenTofu layer differs per cloud. Everything above Kubernetes is identical.

---

## 3. How a change flows down the line

1. **Set up.** `make bootstrap` on a Mac installs pinned tools from a Brewfile and starts a local kind cluster.
2. **Code.** Branch, commit, pull request. Pre-commit hooks catch formatting and leaked secrets before the push.
3. **Build and test.** CI calls the same `make lint test build` the developer ran. Shared steps scan for secrets and risky code.
4. **Review.** Main is protected: one approval from someone else, and green CI.
5. **Package.** After merge, CI builds a multi-arch image (amd64 and arm64), writes an SBOM, scans it, signs it and pushes it by digest. Language packages go to the forge's registries.
6. **Train.** A Kubernetes Job trains the small model on CPU and logs code commit, dataset hash, settings and metrics to MLflow.
7. **Evaluate.** Gates check quality, regression, robustness, fairness, safety, speed and data drift. The limits live in Git.
8. **Register.** Passing versions become candidates. Failing versions stay in the registry, marked rejected, and go no further.
9. **Deploy.** A bot opens a pull request against the environments repo. Dev and staging sync on merge. Staging repeats the speed gate on each cloud's chips.
10. **Release.** A maintainer approves production. A canary takes 10, then 50, then 100 percent of traffic, checking latency and errors at each step.
11. **Observe.** Metrics, logs and drift scores flow to Grafana. A failed canary reverts by itself. Anything else is `git revert`.
12. **Share.** The portal catalog, docs and chat feed update from the same events.

---

## 4. Recommended stack

| Job | Pick | Why this one |
|---|---|---|
| Sign-in | Keycloak | Mature OIDC, groups become roles everywhere |
| Code, reviews, packages | Forgejo | One binary, registries for all five languages |
| CI | Forgejo Actions or Woodpecker | Little to operate, YAML stays thin |
| Images and signing | Harbor, Syft, Grype or Trivy, cosign | Scan, sign, replicate to each cloud |
| Data | DVC on cloud buckets | Git-like, no server |
| Experiments and registry | MLflow | The standard, works with any framework |
| Model testing | pytest, lm-evaluation-harness or Inspect, Fairlearn, Evidently, garak, k6 | Covers quality, fairness, safety, speed, drift |
| Serving | ONNX Runtime or llama.cpp in a plain container | Simple and fast on CPU |
| Infrastructure | OpenTofu | Open-source, runs Terraform code |
| Machines and scripts | Ansible, shell, `factoryctl` | One wrapper over az, gcloud, aws |
| Delivery | Argo CD, Argo Rollouts, Helm, Kustomize | GitOps with automatic rollback |
| Secrets | External Secrets plus cloud secret managers, SOPS | No vault to run |
| Observability | Prometheus, Grafana, Loki, OpenTelemetry | The standard |
| Knowledge | Static portal, MkDocs, ADRs, Zulip | Hours to set up |
| Mac setup | Brewfile, mise, Colima, kind, devcontainers | Free and scriptable |

Language toolchains: **Java** Maven or Gradle, JUnit 5, Testcontainers, JaCoCo, SpotBugs. **C/C++** CMake presets, Conan 2, GoogleTest, clang-tidy, ASan/UBSan. **Python** uv, pytest, ruff, mypy. **Go** `go test -race`, golangci-lint, govulncheck. **Rust** cargo nextest, clippy, cargo-audit. **Web** Vite, Vitest, Playwright, ESLint, axe-core, Lighthouse CI, OWASP ZAP.

---

## 5. Three ways to host the factory itself

| Option | Good for | Pros | Cons |
|---|---|---|---|
| **A. One VM with Docker Compose** | Up to about 20 developers, or a pilot | Running in a day. One Ansible playbook. Easy backups. | Single point of failure. You will migrate later. |
| **B. Hub cluster plus spokes** (recommended) | Most teams | Tools scale and heal. Same skills as the workloads. | Needs Kubernetes knowledge from day one. |
| **C. A full factory in every cloud** | Strict data-residency rules | No cross-cloud dependency. | Three of everything to patch and pay for. |

Start with A if you are unsure. Keep every tool's config in Git from the first day so moving to B is a redeploy, not a rebuild.

---

## 6. Multi-cloud: what actually differs

Kubernetes hides most differences. These are the ones that leak through.

| Concern | Azure AKS | Google GKE | AWS EKS |
|---|---|---|---|
| kubectl login | `kubelogin` | `gke-gcloud-auth-plugin` | `aws eks get-token`, access entries |
| Pod identity | Workload Identity (Entra) | Workload Identity Federation | EKS Pod Identity (or IRSA) |
| Registry next to the cluster | ACR | Artifact Registry | ECR |
| Bucket for data and state | Blob Storage | Cloud Storage | S3 |
| arm64 CPU nodes | Cobalt | Axion | Graviton |
| Node scaling | Cluster autoscaler or node auto-provisioning | Autopilot or node auto-provisioning | Karpenter or Auto Mode |

**Hide the differences in two places only.**

1. OpenTofu modules with identical outputs. `cluster-aks`, `cluster-gke` and `cluster-eks` all return the same things: cluster endpoint, registry URL, bucket name, identity for CI, identity for Argo CD. Everything downstream reads those outputs and never asks which cloud it is on.
2. `factoryctl`, a small shell wrapper. `factoryctl login aks-staging` runs the right CLI and auth plugin for that cluster.

Suggested repository layout:

```
factory/
  Brewfile  .mise.toml  Makefile     Mac bootstrap and the pipeline contract
  bin/factoryctl                     one wrapper for az, gcloud, aws, kubectl
  infra/modules/cluster-{aks,gke,eks}/   same outputs from each
  infra/live/{azure,gcp,aws}/{staging,prod}/   one state file each
  ansible/roles/{mac_dev,ci_runner,docker_host}/
  platform/                          Helm values for the shared tools
  environments/{local,dev,staging,prod}/  desired state, pulled by Argo CD
  templates/{python,java,cpp,go,rust,web,model}/  golden-path starters
  policies/{gates.yaml,rbac.yaml,kyverno/}
  access/groups.yaml                 who is in which team and role
  docs/{adr,runbooks}/
```

---

## 7. Design patterns that keep it simple

1. **Everything as code.** Infrastructure, pipelines, access, gates and deployments are files in Git. Every change has an author, a reviewer and an undo.
2. **One pipeline contract.** Every repo offers `make setup lint test build`. CI calls make. A Mac and the runner behave the same, and a new language is just a new Makefile.
3. **Build once, promote by digest.** The image tested in staging is byte for byte the image in production. Tags can move; digests cannot.
4. **Golden paths.** One template repo per language with the Makefile, Dockerfile, pipeline and owner file already in place. The easy way is the right way.
5. **Thin cloud seam.** Cloud-specific code lives only in OpenTofu modules and `factoryctl`.
6. **Pull-based GitOps.** Each cluster pulls its desired state. No central system holds credentials for every cloud.
7. **Policy as data.** Gates, roles and admission rules are small YAML files, changed by pull request.
8. **Tools behind adapters.** Scripts call `factoryctl`, not Forgejo or Harbor directly, so swapping a tool later touches one file. The simulator is built the same way: one class per tool type.
9. **Lineage in four values.** Code commit, dataset hash, model version, artifact digest. With these you can rebuild or roll back anything.
10. **Small models ride in the image.** With CPU-only models of tens of megabytes, shipping the model inside the container means one digest rolls back code and model together.

---

## 8. Access management and single sign-on

**Five roles, as Keycloak groups.** `factory-admin`, `maintainer`, `developer`, `viewer`, plus bot accounts. Team membership is a second group (`team-nlp`). Every tool reads the same `groups` claim from the token and maps it to its own permissions. The portal's Sign-in view shows the full mapping.

**Day-to-day.**
- Onboarding is a pull request that adds a name to `access/groups.yaml`.
- Offboarding is `factoryctl offboard <user>`. It disables the Keycloak account, then removes SSH keys, personal tokens, robot secrets and cloud bindings in every tool, because disabling the account alone does not revoke those.
- Each tool keeps one local break-glass admin. Its password is sealed, and using it raises an alert.
- Bots never hold long-lived cloud keys. CI runners and Argo CD use each cloud's workload identity.

**Does the free edition do SSO?** Check this before adopting any tool.

| Tool | SSO in the open-source edition | How |
|---|---|---|
| Forgejo | Yes | OIDC login source, groups mapped to teams |
| Woodpecker | Through the forge | Logs in with Forgejo OAuth |
| Harbor | Yes | OIDC mode, groups mapped to project roles. Choose it at install. |
| MLflow | No | Put oauth2-proxy in front |
| Argo CD | Yes | OIDC, roles by group in `policy.csv` |
| Grafana | Yes | Generic OAuth with role mapping. Team sync is paid. |
| Zulip | Yes | OIDC or SAML |
| kubectl | Differs per cloud | People mostly use Argo CD and Grafana instead. Keep kubectl for the platform team. |
| Cloud consoles | By federation | Federate Keycloak with Entra ID, Google Workforce Identity Federation and AWS IAM Identity Center. Budget real time for this. |

---

## 9. Tracking change and rolling back

| What | How it is tracked | How to roll back | Gotcha |
|---|---|---|---|
| Code | Git commits and pull requests | `git revert` | Never rewrite main |
| Deployments | Commits in the environments repo | `git revert`, Argo CD syncs the old digest | With auto-sync on, `argocd app rollback` is refused |
| A bad release in progress | Argo Rollouts analysis | Automatic abort | Needs good metrics and sensible limits |
| Models | MLflow versions and the `champion` alias | Re-pin the previous version in Git | Do not resolve aliases at runtime |
| Data | DVC hashes | Check out the old `.dvc` file | Buckets need versioning switched on |
| Infrastructure | OpenTofu state and Git | Revert and apply | No true undo. Protect stateful resources with `prevent_destroy` and backups. |
| Databases | Migration files | Expand, then contract | A rollback that drops a column loses data |
| Access | `access/groups.yaml` | Revert the pull request | Tokens issued earlier live until they expire |
| Everything | One audit trail | Not applicable | Ship every tool's audit log to Loki |

---

## 10. Testing strategy

### Code

Unit tests on every push, integration tests with Testcontainers or Docker Compose, contract tests between services, and browser tests with Playwright for the web app. Add axe-core for accessibility, Lighthouse CI for page speed, k6 for load, and an OWASP ZAP baseline scan against staging.

### Models, on CPU

| Tier | When | Time budget | What |
|---|---|---|---|
| Smoke | Every commit, on a Mac and in CI | Under 2 minutes | Tiny golden set, schema checks, one latency probe |
| Full gates | Every candidate | 10 to 40 minutes on CPU | Quality, regression, robustness, fairness, safety, speed, drift |
| Per-cloud speed | Staging | A few minutes per cluster | The same speed gate on each cloud's chips |
| Canary | Production | 15 to 30 minutes | Real traffic at 10, 50, 100 percent |
| Continuous | Always | Ongoing | Drift and quality sampled in production |

**CPU-specific practices.**
- Fix the thread count (`OMP_NUM_THREADS`, `torch.set_num_threads`) to match the pod's CPU request. Oversubscribed threads are the most common cause of bad tail latency.
- Set CPU requests equal to limits for model pods, or the kernel throttles them mid-request.
- Measure speed under production-like concurrency, not one request at a time. The simulator's v2 story exists to make this point.
- Run speed gates on a dedicated runner. Shared runners make latency numbers meaningless.
- Test the file you ship. Quantizing to int8 changes accuracy a little, so the gates must run on the ONNX or GGUF file.
- On a Mac, force `device="cpu"`. PyTorch can pick MPS and give different numbers from the cloud.
- Assert inside a tolerance band. x86 and arm64 produce slightly different floating-point results.

---

## 11. Top gotchas, as a checklist

**Licences that changed.** Terraform and Vault are BSL (use OpenTofu and OpenBao). Seldon Core is BSL. MinIO's community edition is no longer maintained (use SeaweedFS, Garage or cloud buckets). Bitnami's free versioned images and charts stopped in August 2025 (use upstream charts). Docker Desktop needs a paid licence at larger companies (use Colima or Podman). ingress-nginx is retired (use a Gateway API implementation).

**Supply chain.** Pin CI actions and images by commit or digest, scanners included. The March 2026 Trivy compromise spread through unpinned references. Proxy dependencies through your own registry. Verify signatures at admission, not just at build.

**Sign-in.** Keycloak is a single point of failure: two replicas, database backups, break-glass accounts. Check each tool's free edition for SSO. Script offboarding.

**Multi-cloud.** Three auth plugins, three pod-identity systems, different storage classes. Keep Kubernetes versions aligned. Replicate images to each cloud's registry to avoid cross-cloud transfer fees and slow pulls.

**Mac versus cloud.** arm64 laptop, mostly amd64 cloud: build multi-arch. kind has no real load balancer, storage classes or IAM, so staging on real clusters stays mandatory.

**Operations.** Back up the forge, Keycloak, MLflow's database and the buckets, and rehearse a restore. Set registry retention before the disk fills. Put an expiry date on every security exception.

---

## 12. Rollout plan

| Phase | Weeks | Deliver |
|---|---|---|
| 1. Foundations | 1 to 2 | Keycloak, Forgejo, runners, Mac bootstrap, one template repo, the portal |
| 2. Supply chain | 3 to 4 | Harbor, SBOM, scanning, signing, branch protection everywhere |
| 3. First cloud | 5 to 6 | OpenTofu module for one cloud, Argo CD, environments repo, dev and staging |
| 4. Model line | 7 to 9 | DVC, MLflow behind oauth2-proxy, the gate suite, canary with automatic rollback |
| 5. Other clouds | 10 to 12 | The remaining two modules, image replication, per-cloud speed gates |
| 6. Harden | Ongoing | Backup drills, admission policies, cost reports, templates for the remaining languages |

Move one real team through each phase before starting the next. A factory nobody uses is only a cost.

---

## 13. Words used here

- **Artifact.** A built file you can deploy: an image, a package, a model file.
- **Canary.** Sending a small share of real traffic to a new version first, and watching it.
- **Champion.** The model version currently serving production.
- **Digest.** A fingerprint of an image's exact contents. It cannot be moved the way a tag can.
- **Drift.** Live input data slowly becoming different from the data the model was trained on.
- **Gate.** An automatic check with a numeric limit that a model must pass to move on.
- **GitOps.** The cluster copies what Git says. To change the cluster, change Git.
- **Golden set.** A carefully labelled test dataset the model never sees in training.
- **OIDC.** The login standard that lets one identity provider sign you in to many tools.
- **p95 latency.** 95 out of 100 requests finish faster than this number.
- **Quantization.** Storing model numbers in 8 bits instead of 32, making the model smaller and faster on CPU.
- **SBOM.** Software bill of materials: the parts list of an image.
- **Workload identity.** A pod proves who it is to the cloud without any stored password.
