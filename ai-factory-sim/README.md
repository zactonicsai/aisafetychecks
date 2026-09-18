# AI factory simulator

A software factory for building and testing small CPU-only AI models, simulated with plain Python and one static HTML page. It shows every tool type working together before you install any of them.

## Quick start (macOS)

```sh
python3 factory_sim.py run      # play one simulated week, write site/index.html
open site/index.html            # the portal: one view per tool type
```

Nothing to install. It uses only the Python standard library and runs on the `python3` that ships with macOS (3.9 or newer).

Other commands:

```sh
python3 factory_sim.py run --seed 7   # same story, different numbers
python3 factory_sim.py run --quiet    # skip the event log
python3 factory_sim.py serve          # serve the portal at http://localhost:8080
python3 factory_sim.py tools          # print tool options, pros, cons, gotchas
```

## What is in the folder

| File | What it is |
|---|---|
| `ARCHITECTURE.md` | The design: layers, flow, multi-cloud, patterns, access, rollback, testing, gotchas, rollout plan |
| `TOOL_OPTIONS.md` | Every tool type with its default pick, alternatives, pros, cons and gotchas. Generated. |
| `catalog.py` | The source of `TOOL_OPTIONS.md` and the portal's Tool options view. Edit tool advice here. |
| `factory_sim.py` | The simulator. One small class per tool type, one scenario, one JSON document out. |
| `portal.template.html` | The static portal. The simulator injects its JSON into this file. |
| `site/index.html` | The generated portal. Self-contained, works from `file://`. |
| `site/factory_state.json` | The raw simulated state, for your own scripts. |

## What the simulation covers

| Tool type | Standing in for | Where to look in the portal |
|---|---|---|
| Single sign-on and roles | Keycloak | Sign-in and access, plus the user menu in the header |
| Code, reviews, packages | Forgejo | 1 Code |
| CI for Java, C/C++, Python, Go, Rust, web | Forgejo Actions or Woodpecker | 2 Build and test |
| Registry, SBOM, scanning, signing | Harbor, Syft, Grype, cosign | 3 Scan and sign |
| Data versions and experiment tracking | DVC, MLflow | 4 Train |
| Model testing gates | pytest, Fairlearn, garak, k6, Evidently | 5 Evaluate |
| Model registry and lineage | MLflow | 6 Register |
| GitOps, canary, rollback | Argo CD, Argo Rollouts | 7 Deploy |
| Metrics, drift, alerts | Prometheus, Grafana | 8 Observe |
| Infrastructure and cloud CLIs | OpenTofu, Ansible, az, gcloud, aws | Infrastructure |
| Catalog, decisions, chat | Portal, ADRs, Zulip | Shared knowledge |
| Change tracking | One audit log | Audit trail |

Targets: `mac-kind`, `docker-dev`, then staging and prod on AKS, GKE and EKS.

## Change the story

Everything that looks like policy is plain data at the top of `factory_sim.py`:

- `USERS` and `ROLES`: who exists and what each role may do.
- `REPOS` and `TOOLCHAINS`: the repos and each language's make targets.
- `TARGETS`: where things deploy, with the real commands for each.
- `GATES` and `CANARY_LIMITS`: the numbers a model must meet.
- `MODEL_STORY`: the four model versions and what happens to each.

Try raising the Fairness limit to `0.10` and run again: v3 now passes its gates and goes to canary.

## From simulated to real

Each station class has the same shape as the real integration. To go real, keep the scenario and swap one class at a time for an adapter that shells out:

| Station class | Real adapter calls |
|---|---|
| `Identity` | Keycloak admin API, or `kcadm.sh` |
| `Forge` | `git`, Forgejo API |
| `CI` | `make` inside the toolchain image |
| `Registry` | `docker buildx`, `syft`, `grype`, `cosign` |
| `ModelHub` | `dvc`, MLflow Python client, `pytest` |
| `Infra` | `tofu`, `ansible-playbook`, `az`, `gcloud`, `aws` |
| `Delivery` | `git` on the environments repo, `argocd`, `kubectl argo rollouts` |

Order that works well: `Infra` for the local kind target first, then `Forge` and `CI`, then `Registry`, then `ModelHub`, then `Delivery`, then the clouds.
