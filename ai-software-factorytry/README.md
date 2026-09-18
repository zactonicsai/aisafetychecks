# Aether Forge — Open Source AI Model Testing Software Factory

A layered, GitOps-first software factory for building, testing, sharing, and deploying AI models and multi-language software (Python, Java, C/C++, Go, Rust, web).

This repository contains:

1. Architecture, tool choices, flows, design patterns, pros/cons, and gotchas (`ARCHITECTURE.md`)
2. Infrastructure blueprints (OpenTofu, Ansible, shell, cloud CLIs, sample pipelines)
3. A **local simulation** (`simulation/`) — Python API + static HTML factory floor

> Azure does **not** have EKS. EKS is AWS. Azure’s managed Kubernetes is **AKS**. This factory treats AWS EKS, Azure AKS, and GCP GKE as interchangeable Kubernetes substrates.

## Quick start (simulation)

```bash
cd simulation
python3 app.py
# stdlib only — no pip install required
```

Open http://127.0.0.1:8080

Default users (simulated SSO):

| User | Role | Password |
|------|------|----------|
| `ada` | platform-admin | `forge` |
| `linus` | developer | `forge` |
| `grace` | ml-engineer | `forge` |
| `ken` | reviewer | `forge` |

## What the factory gives a developer

1. A Linux workspace (VM / CDE / container) with toolchains preinstalled
2. Pull extra tools from the internal package repo (apt/yum + language registries)
3. Write code and unique test tools
4. Check in to Git (Forgejo)
5. Compose a pipeline: **build → unit/integration test → model eval / stage test → image → deploy**
6. Deploy to Docker/Podman locally, then the same image to k3s / AKS / GKE / EKS
7. Track versions, promote, and roll back from Git + the model/image registry
8. One Keycloak SSO session across Git, CI, registries, notebooks, chat, and dashboards
