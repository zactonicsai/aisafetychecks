"""
catalog.py - what the factory is made of.

One entry per tool type. Each entry names the default pick, the alternatives
with pros and cons, and the gotchas that bite in practice.

This file is the single source of truth. `factory_sim.py run` reads it to
build both the "Tool options" view in the portal and TOOL_OPTIONS.md, so you
only ever edit tool advice in one place.

Scope: CPU only, small models, no GPUs. Every pick is open source; licence
notes flag the projects whose terms changed recently (checked September 2026).
"""

CATALOG = [
    dict(
        id="identity", layer="Sign-in and access",
        job="One login for every tool. Groups decide who can do what.",
        pick="Keycloak", licence="Apache-2.0",
        options=[
            dict(name="Keycloak", pros="Mature OIDC and SAML, fine-grained groups, large community.",
                 cons="Heaviest to run. Major upgrades arrive often and need care."),
            dict(name="Authentik", pros="Friendlier admin UI. Built-in proxy for apps that have no SSO.",
                 cons="Smaller ecosystem. Some features are enterprise-only."),
            dict(name="Dex or Authelia", pros="Tiny footprint.",
                 cons="No real user management: you still need a directory behind them."),
        ],
        gotchas=[
            "If the identity provider is down, nobody can log in anywhere. Run two replicas, back up its database, and keep one sealed break-glass admin account in each tool.",
            "Disabling a user does not revoke their SSH keys, personal tokens or robot accounts inside each tool. Offboarding must be a script that visits every tool.",
            "Many open-core tools charge for SSO or group sync. Check the free edition before adopting a tool.",
            "Keep the realm as code (keycloak-config-cli or the OpenTofu provider) so access changes are reviewed pull requests.",
        ],
    ),
    dict(
        id="source", layer="Code, reviews and packages",
        job="Git hosting, pull requests, and the package registries for every language.",
        pick="Forgejo", licence="GPL-3.0-or-later",
        options=[
            dict(name="Forgejo (or Gitea)", pros="One small binary. Built-in registries for Maven, PyPI, Cargo, Go, Conan, npm, containers and Helm. OIDC login.",
                 cons="Fewer enterprise controls. Smaller plugin ecosystem."),
            dict(name="GitLab CE", pros="Code, CI, registry and issues in one product. Very mature CI.",
                 cons="Wants 8 GB RAM or more. Many approval and access features sit in paid tiers."),
        ],
        gotchas=[
            "Protect main on day one: one review from someone else plus green CI.",
            "Git is the source of truth for deployments too, so mirror and back up the forge nightly.",
            "Datasets and model files do not belong in Git. Use DVC and object storage.",
            "Forgejo Actions reads GitHub-style workflows, but not every marketplace action works. Keep workflows thin.",
        ],
    ),
    dict(
        id="ci", layer="CI runners",
        job="Runs the same make targets a developer runs on a Mac, on every push.",
        pick="Forgejo Actions or Woodpecker CI", licence="GPL-3.0 / Apache-2.0",
        options=[
            dict(name="Forgejo Actions or Woodpecker", pros="Simple, container-native, little to operate.",
                 cons="Fewer features than the big engines."),
            dict(name="Jenkins", pros="Does anything. A plugin exists for everything.",
                 cons="Plugin and security upkeep never ends. Groovy pipelines get hard to read."),
            dict(name="Tekton or Argo Workflows", pros="Kubernetes-native. Good for training jobs shaped like graphs.",
                 cons="Verbose YAML and a steep learning curve."),
            dict(name="Dagger", pros="Pipelines as code that run the same on a Mac and in CI.",
                 cons="One more engine to learn and host."),
        ],
        gotchas=[
            "Keep pipeline YAML thin. Logic lives in the Makefile so a Mac and CI run the same commands.",
            "Pin actions and images by commit SHA or digest, scanners included. In March 2026 hijacked Trivy action tags stole CI secrets and led to poisoned LiteLLM releases on PyPI.",
            "A runner with the Docker socket mounted is root on its host. Use rootless BuildKit or throwaway runners.",
            "Proxy and cache dependencies through your own registry, or builds crawl and break when the internet hiccups.",
            "Latency tests are flaky on shared runners. Give speed gates a dedicated runner with fixed CPU.",
        ],
    ),
    dict(
        id="artifacts", layer="Images, packages and signatures",
        job="Stores what CI builds, scans it, signs it, and copies it next to each cluster.",
        pick="Harbor plus the forge's package registries", licence="Apache-2.0",
        options=[
            dict(name="Harbor", pros="Scanning, signing policy, OIDC, and replication to ACR, Artifact Registry and ECR.",
                 cons="Several services plus Postgres and Redis to run."),
            dict(name="Forge built-in registry only", pros="No extra tool.",
                 cons="No scanning, admission policy or replication."),
            dict(name="Zot", pros="Tiny OCI-native registry.", cons="Fewer features and a smaller community."),
            dict(name="Cloud registries alone", pros="Managed and close to the clusters.",
                 cons="Three places to manage, and not open source."),
        ],
        gotchas=[
            "Pulling images across clouds costs money and time. Replicate to the registry beside each cluster.",
            "Deploy by digest, never by tag. A tag can move; a digest cannot.",
            "Harbor's login mode cannot be switched once users exist. Choose OIDC at install.",
            "Set retention and garbage collection early or the disk fills.",
        ],
    ),
    dict(
        id="security", layer="Supply-chain checks",
        job="Finds leaked secrets, risky code and vulnerable dependencies before anything ships.",
        pick="Gitleaks, Opengrep, Syft + Grype or Trivy, cosign, Kyverno, ZAP", licence="MIT / LGPL / Apache-2.0",
        options=[
            dict(name="Trivy", pros="One tool for images, IaC, SBOMs and secrets.",
                 cons="Its releases and actions were compromised in March 2026. Pin exact versions and digests."),
            dict(name="Syft + Grype", pros="Clean split: build the SBOM once, scan it many times.", cons="Two tools instead of one."),
            dict(name="SonarQube Community Build", pros="Quality gates for many languages in one UI.",
                 cons="Branch and pull-request analysis is paid."),
        ],
        gotchas=[
            "Scanners are software too. Pin them and verify them like any other dependency.",
            "Block criticals that have a fix. Blocking everything stops the line daily and teaches people to bypass it.",
            "Keep the ignore list in Git with an expiry date on every entry.",
            "Signing without verifying is theatre. Enforce signatures at admission with Kyverno.",
        ],
    ),
    dict(
        id="data", layer="Data and object storage",
        job="Versions datasets so any model can be traced to the exact data that trained and tested it.",
        pick="DVC on each cloud's bucket (S3, GCS, Azure Blob)", licence="Apache-2.0",
        options=[
            dict(name="DVC", pros="Feels like Git. No server. Works with any bucket.",
                 cons="No UI. Slow with millions of tiny files."),
            dict(name="lakeFS", pros="Branch and merge for whole data lakes, with a UI.", cons="Another service to run."),
            dict(name="Git LFS", pros="Simplest possible.", cons="Poor at scale, and fills the forge's disk."),
        ],
        gotchas=[
            "MinIO's community edition is no longer maintained (repository archived April 2026). For self-hosted S3 use SeaweedFS, Garage or Ceph RGW.",
            "Record the dataset hash in every training run. Without it lineage is a guess.",
            "Golden test sets must be held out and access-controlled, or they leak into training.",
        ],
    ),
    dict(
        id="tracking", layer="Experiments and model registry",
        job="Remembers every training run and which model version is the champion.",
        pick="MLflow", licence="Apache-2.0",
        options=[
            dict(name="MLflow", pros="The de facto standard. Tracking, registry and evaluation for any framework.",
                 cons="No OIDC in the open-source server. Plain UI."),
            dict(name="ClearML", pros="Tracking plus orchestration and data management.", cons="Heavier server, some open-core parts."),
            dict(name="Aim", pros="Fast, pleasant run comparison.", cons="No model registry."),
        ],
        gotchas=[
            "Put oauth2-proxy in front of MLflow to get SSO.",
            "Use aliases (champion, candidate). Stages are deprecated.",
            "Pin the model version in Git for each deployment. Do not resolve an alias at runtime, or rollbacks stop being auditable.",
            "Back up both halves: metadata in Postgres and artifacts in the bucket.",
        ],
    ),
    dict(
        id="evaluation", layer="Model testing",
        job="Decides with numbers, not opinions, whether a model may move down the line.",
        pick="pytest golden sets, lm-evaluation-harness or Inspect, Fairlearn, Evidently, garak, k6", licence="MIT / Apache-2.0",
        options=[
            dict(name="pytest plus your own golden sets", pros="Everyone knows it. Runs the same on a Mac and in CI.",
                 cons="You build the metrics and reports yourself."),
            dict(name="lm-evaluation-harness or Inspect AI", pros="Standard benchmarks and agent-style evaluations.",
                 cons="Slow on CPU: run a small subset per commit and the full set nightly."),
            dict(name="promptfoo or DeepEval", pros="Quick prompt and RAG regression tests.",
                 cons="Judge-model costs. promptfoo stays MIT but has belonged to OpenAI since March 2026."),
            dict(name="garak or PyRIT", pros="Red-team probes: jailbreaks, prompt injection, data leakage.", cons="Noisy results that need triage."),
        ],
        gotchas=[
            "Models are not deterministic. Fix seeds and thread counts, and assert within a tolerance band, never equality.",
            "Test the file you ship. Quantizing to int8 shifts accuracy, so gate the ONNX or GGUF artifact, not the training checkpoint.",
            "On a Mac force device='cpu', or PyTorch may quietly use MPS and give different numbers from the cloud.",
            "Thresholds live in Git and change by pull request.",
            "Two tiers: a smoke suite under two minutes on every commit, the full suite on every candidate.",
        ],
    ),
    dict(
        id="serving", layer="Model serving on CPU",
        job="Turns a model file into an HTTP service that is fast enough on ordinary CPUs.",
        pick="ONNX Runtime or llama.cpp in a plain container", licence="MIT",
        options=[
            dict(name="Plain container (FastAPI + ONNX Runtime)", pros="Simplest. Runs the same on Docker, kind and every cloud.",
                 cons="You write the batching and health checks."),
            dict(name="BentoML", pros="Python-first packaging with batching built in.", cons="Another abstraction to learn."),
            dict(name="KServe", pros="Canary, scale to zero, standard inference protocol.", cons="More moving parts than small CPU models need."),
        ],
        gotchas=[
            "Seldon Core moved to a BSL licence in 2024 and is no longer open source.",
            "Kubernetes CPU limits throttle and wreck p95 latency. Set requests equal to limits and match OMP_NUM_THREADS to the request.",
            "Chips differ per cloud (AVX-512 or AMX on x86, NEON on arm64). Measure latency on each cloud, not once.",
            "Small models can ship inside the image, so one digest rolls back code and model together.",
        ],
    ),
    dict(
        id="infra", layer="Infrastructure as code",
        job="Creates the clusters, networks, buckets and identities on each cloud.",
        pick="OpenTofu", licence="MPL-2.0",
        options=[
            dict(name="OpenTofu", pros="Open source. Drop-in for Terraform code and providers. State encryption built in.",
                 cons="The very newest Terraform features can differ."),
            dict(name="Terraform", pros="Largest ecosystem and documentation.", cons="BSL licence, so not open source."),
            dict(name="Pulumi", pros="Real programming languages.", cons="A different model plus a state service."),
            dict(name="Crossplane", pros="Kubernetes-native control plane.", cons="Steep, and needs a cluster before it can build one."),
        ],
        gotchas=[
            "Remote state with locking, one state per cloud per environment. Never local state.",
            "OpenTofu builds the cluster and installs Argo CD, then stops. Do not manage in-cluster apps with it.",
            "There is no real rollback: you revert and apply. Guard stateful resources with prevent_destroy and backups.",
            "Pin provider versions and commit the lock file.",
            "Keep Kubernetes minor versions aligned across AKS, GKE and EKS.",
        ],
    ),
    dict(
        id="config", layer="Machines, scripts and cloud CLIs",
        job="Sets up Macs, runners and the Docker host, and hides three cloud CLIs behind one command.",
        pick="Ansible, shell, and az / gcloud / aws behind factoryctl", licence="GPL-3.0",
        options=[
            dict(name="Ansible", pros="Agentless and readable. Good for Macs, runners and VMs.", cons="Slow across many hosts. Logic in YAML gets ugly."),
            dict(name="Shell scripts", pros="No dependencies.", cons="Hard to keep idempotent. Use set -euo pipefail and shellcheck."),
            dict(name="Packer images", pros="Immutable and fast to boot.", cons="Every change means a rebuild."),
        ],
        gotchas=[
            "Ansible is not for deploying apps to Kubernetes. That is GitOps' job.",
            "kubectl login differs per cloud: AKS needs kubelogin, GKE needs gke-gcloud-auth-plugin, EKS uses aws eks get-token. Wrap all three.",
            "Pin CLI versions with a Brewfile and mise so every Mac and runner matches.",
        ],
    ),
    dict(
        id="delivery", layer="GitOps and safe rollout",
        job="Makes each cluster match what Git says, and rolls back when numbers go bad.",
        pick="Argo CD and Argo Rollouts, Helm + Kustomize", licence="Apache-2.0",
        options=[
            dict(name="Argo CD", pros="Clear UI, SSO, roles by group.", cons="A central hub needs network paths and credentials into every cluster."),
            dict(name="Flux", pros="Pull-only and light. No inbound access needed.", cons="Minimal UI."),
            dict(name="helm upgrade from CI", pros="Simplest.", cons="No drift detection, and CI holds cluster credentials."),
        ],
        gotchas=[
            "With auto-sync on, 'argocd app rollback' is refused. Roll back with git revert.",
            "One Argo CD per cluster, pulling from Git, avoids a hub that holds the keys to every cloud.",
            "ingress-nginx was retired in March 2026. Use a Gateway API implementation such as Envoy Gateway, Traefik or Cilium.",
            "Bitnami stopped publishing free versioned images and charts in August 2025. Use upstream charts and operators such as CloudNativePG.",
        ],
    ),
    dict(
        id="secrets", layer="Secrets",
        job="Keeps passwords and keys out of Git and out of CI variables.",
        pick="External Secrets Operator with each cloud's secret manager; SOPS + age for Git", licence="Apache-2.0 / MPL-2.0",
        options=[
            dict(name="External Secrets + cloud secret managers", pros="No vault to run. Uses workload identity.", cons="Three backends to understand."),
            dict(name="SOPS + age", pros="Encrypted secrets in Git. Very simple.", cons="You distribute keys by hand. No rotation or audit trail."),
            dict(name="OpenBao", pros="Open-source fork of Vault: dynamic secrets and auditing.", cons="One more highly-available service."),
        ],
        gotchas=[
            "CI reaches each cloud through workload identity. Store no long-lived cloud keys.",
            "Workload identity comes in three flavours (AKS Workload Identity, GKE Workload Identity Federation, EKS Pod Identity). Hide them behind module outputs.",
            "HashiCorp Vault is BSL-licensed. OpenBao is the open-source line.",
        ],
    ),
    dict(
        id="observability", layer="Metrics, logs and drift",
        job="Shows whether services and models are healthy, and wakes someone when they are not.",
        pick="Prometheus, Grafana, Loki, OpenTelemetry, Evidently", licence="Apache-2.0 / AGPL-3.0",
        options=[
            dict(name="Prometheus + Grafana + Loki", pros="The standard. Dashboards exist for everything.", cons="Grafana and Loki are AGPL: fine to use, relevant if you modify and resell."),
            dict(name="VictoriaMetrics", pros="Lighter, with cheaper long-term storage.", cons="Smaller community."),
            dict(name="SigNoz", pros="Metrics, logs and traces in one product.", cons="Younger project."),
        ],
        gotchas=[
            "Grafana OSS maps roles from OIDC claims, but team sync is an enterprise feature.",
            "Run one metrics stack per cluster and remote-write to the hub. Never scrape across clouds.",
            "Model quality and drift are production metrics. Alert on them exactly like error rates.",
        ],
    ),
    dict(
        id="knowledge", layer="Portal, docs and chat",
        job="Lets one team find, understand and reuse what another team built.",
        pick="A static portal first, MkDocs + ADRs in Git, Zulip", licence="Apache-2.0",
        options=[
            dict(name="Static portal (like this one)", pros="Hours to set up and nothing to patch.", cons="No templates or scorecards engine."),
            dict(name="Backstage", pros="Catalog, templates, docs and plugins.", cons="It is a framework you build and upgrade, so it needs a TypeScript owner. Worth it past roughly 50 services."),
            dict(name="Wiki.js or BookStack", pros="Friendly editing for everyone.", cons="Docs drift away from the code."),
        ],
        gotchas=[
            "Mattermost's free edition has no generic OIDC login. Zulip does.",
            "Keep docs beside the code, or they rot.",
            "Put an owner file in every repo from day one.",
        ],
    ),
    dict(
        id="localdev", layer="Local development on macOS",
        job="Gives every developer the same tools and a small copy of the platform on a laptop.",
        pick="Brewfile, mise, Colima, kind, devcontainers, pre-commit", licence="MIT / Apache-2.0",
        options=[
            dict(name="Colima", pros="Free, light, command-line.", cons="No GUI."),
            dict(name="Podman Desktop or Rancher Desktop", pros="GUI, with Kubernetes built in.", cons="Occasional compatibility quirks."),
            dict(name="Docker Desktop", pros="Smoothest experience.", cons="Paid licence for larger companies, and not open source."),
        ],
        gotchas=[
            "Apple Silicon is arm64 and most cloud nodes are amd64. Build multi-arch images; emulating amd64 on a Mac is slow.",
            "arm64 cloud nodes (Graviton, Cobalt, Axion) match the Mac and cost less. Worth a staging pool.",
            "kind is not a cloud: no real load balancers, storage classes or IAM. Staging on real clusters stays mandatory.",
        ],
    ),
]


def as_markdown():
    """Render the catalogue as TOOL_OPTIONS.md."""
    out = [
        "# Tool options, pros, cons and gotchas",
        "",
        "Generated from `catalog.py` by `python3 factory_sim.py run`. Edit the catalogue, not this file.",
        "",
        "Scope: CPU only, small models, no GPUs. Every default pick is open source.",
        "",
    ]
    for c in CATALOG:
        out += [f"## {c['layer']}", "", c["job"], "", f"**Default pick:** {c['pick']} ({c['licence']})", "",
                "| Option | Pros | Cons |", "|---|---|---|"]
        out += [f"| {o['name']} | {o['pros']} | {o['cons']} |" for o in c["options"]]
        out += ["", "**Gotchas**", ""]
        out += [f"- {g}" for g in c["gotchas"]]
        out += [""]
    return "\n".join(out)
