#!/usr/bin/env python3
"""
factory_sim.py - an AI model testing software factory, simulated.

Standard library only. Runs on the python3 that ships with macOS (3.9+).

    python3 factory_sim.py run             # play the scenario, write site/index.html
    python3 factory_sim.py run --seed 7    # same story, different numbers
    python3 factory_sim.py serve           # serve ./site at http://localhost:8080
    python3 factory_sim.py tools           # print the tool catalogue

How it is built (and how the real factory should be built):

* Every tool type is one small class, a "station". A station talks only to
  the shared Sim (clock, random numbers, audit log) and asks Identity before
  it does anything. To go real, replace a station with an adapter that shells
  out to tofu, ansible-playbook, az, gcloud, aws, kubectl, helm or mlflow.
  The scenario does not change.
* Policy is data: ROLES, GATES, TARGETS and TOOLCHAINS below are what you
  would keep in Git and change by pull request.
* Everything that happens lands in one append-only audit log. The portal is
  just a view of that log and of each station's state.

Scope: CPU only, small models, no GPUs.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import random
import socketserver
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from catalog import CATALOG, as_markdown

HERE = Path(__file__).resolve().parent
MODEL = "intent-classifier"


# --------------------------------------------------------------------------
# Policy as data. In the real factory these live in Git.
# --------------------------------------------------------------------------

USERS = [
    dict(id="ana", team="platform", role="factory-admin"),
    dict(id="raj", team="platform", role="maintainer"),
    dict(id="noor", team="platform", role="developer"),
    dict(id="mei", team="vision", role="maintainer"),
    dict(id="tom", team="vision", role="developer"),
    dict(id="lea", team="nlp", role="maintainer"),
    dict(id="sam", team="nlp", role="developer"),
    dict(id="zoe", team="web", role="maintainer"),
    dict(id="ben", team="web", role="developer"),
    dict(id="kai", team="risk", role="viewer"),
    dict(id="bot-ci", team="platform", role="ci-bot", bot=True),
    dict(id="bot-gitops", team="platform", role="gitops-bot", bot=True),
]

DEV_PERMS = ["repo:read", "repo:write", "pr:review", "pr:merge", "ci:run", "artifact:read", "data:write",
             "model:train", "deploy:local", "deploy:dev", "obs:read", "docs:write"]


def _tools(forgejo, harbor, mlflow, argocd, grafana, clouds):
    return dict(Forgejo=forgejo, Harbor=harbor, MLflow=mlflow, **{"Argo CD": argocd}, Grafana=grafana, Clouds=clouds)


ROLES = {
    "factory-admin": dict(
        about="Runs the platform. Two or three people, used rarely.", perms=["*"],
        tools=_tools("Site admin", "System admin", "Admin", "role:admin", "Admin", "Owner, break-glass only")),
    "maintainer": dict(
        about="Owns a team's repos, models and what reaches production.",
        perms=DEV_PERMS + ["model:promote", "deploy:staging", "deploy:prod"],
        tools=_tools("Team owner: merge, protect branches", "Project maintainer", "Manage team models",
                     "role:deployer", "Editor", "Read-only console")),
    "developer": dict(
        about="Builds, tests and ships to dev. Cannot touch production.", perms=DEV_PERMS,
        tools=_tools("Write to team repos", "Project developer", "Edit team experiments",
                     "role:dev, sync dev only", "Editor", "None")),
    "viewer": dict(
        about="Read-only. Auditors, risk and managers.", perms=["repo:read", "artifact:read", "obs:read"],
        tools=_tools("Read", "Guest", "Read", "role:readonly", "Viewer", "None")),
    "ci-bot": dict(
        about="The CI runner's identity. Short-lived tokens only.",
        perms=["repo:read", "ci:run", "artifact:read", "artifact:push", "model:register"],
        tools=_tools("Robot token: read repos", "Robot account: push", "Service token: register runs",
                     "None", "None", "Workload identity: push to registries")),
    "gitops-bot": dict(
        about="Argo CD's identity. Syncs what Git says, on its own up to staging.",
        perms=["repo:read", "artifact:read", "deploy:dev", "deploy:staging"],
        tools=_tools("Deploy key: read environments repo", "Robot account: pull", "None",
                     "Application controller", "None", "Workload identity per cluster")),
}

REPOS = [
    dict(name="model-trainer", lang="python", team="nlp", kind="training job", about="Trains, quantizes and exports the intent model"),
    dict(name="fast-tokenizer", lang="rust", team="nlp", kind="library", about="Tokenizer shared by training and serving"),
    dict(name="inference-engine", lang="cpp", team="vision", kind="service", about="ONNX Runtime server tuned for CPU"),
    dict(name="feature-service", lang="java", team="platform", kind="service", about="Looks up customer features for each request"),
    dict(name="model-gateway", lang="go", team="platform", kind="service", about="Routes traffic between model versions"),
    dict(name="eval-dashboard", lang="web", team="web", kind="web app", about="Shows evaluation results to every team"),
]
DEPLOYABLE = ("service", "web app")

# One pipeline contract: every repo offers the same make targets, so CI and a Mac run the same thing.
TOOLCHAINS = {
    "python": dict(
        label="Python", image="python:3.13-slim", pkg="PyPI", secs=(40, 95),
        steps=[("setup", "uv sync --frozen"), ("lint", "ruff check . && mypy src"),
               ("test", "pytest -q --cov=src --cov-fail-under=80"), ("build", "uv build")],
        tools="uv, ruff, mypy, pytest, coverage, hypothesis",
        gotcha="Lock with uv.lock. PyTorch wheels differ for x86, arm64 and Apple Silicon: choose the CPU index per platform."),
    "java": dict(
        label="Java", image="eclipse-temurin:25-jdk", pkg="Maven", secs=(70, 150),
        steps=[("setup", "./mvnw -B -q dependency:go-offline"), ("lint", "./mvnw -B spotless:check spotbugs:check"),
               ("test", "./mvnw -B verify   # JUnit 5 + JaCoCo"), ("build", "./mvnw -B package -DskipTests")],
        tools="Maven or Gradle, JUnit 5, Mockito, Testcontainers, JaCoCo, SpotBugs",
        gotcha="Pin the JDK with the wrapper and toolchains. Testcontainers needs a container runtime on the runner."),
    "cpp": dict(
        label="C and C++", image="factory/cpp-toolchain:clang", pkg="Conan", secs=(120, 260),
        steps=[("setup", "conan install . --build=missing -pr:h=profiles/linux-amd64"),
               ("lint", "clang-format --dry-run -Werror src && clang-tidy -p build src/*.cpp"),
               ("test", "cmake --preset asan && ctest --preset asan   # GoogleTest + ASan/UBSan"),
               ("build", "cmake --preset release && cmake --build --preset release")],
        tools="CMake presets, Conan 2, GoogleTest or Catch2, clang-tidy, ASan and UBSan, llvm-cov, ccache",
        gotcha="Macs are arm64 and most cloud nodes are amd64. Keep a Conan profile per platform and never ship a laptop build."),
    "go": dict(
        label="Go", image="golang:1.26", pkg="Go module", secs=(30, 80),
        steps=[("setup", "go mod download"), ("lint", "go vet ./... && golangci-lint run"),
               ("test", "go test -race -cover ./... && govulncheck ./..."), ("build", "CGO_ENABLED=0 go build ./cmd/...")],
        tools="go test -race, testify, golangci-lint, govulncheck",
        gotcha="Set GOFLAGS=-mod=readonly and GOPRIVATE for the forge. CGO complicates cross-compiling; avoid it if you can."),
    "rust": dict(
        label="Rust", image="rust:stable-slim", pkg="Cargo", secs=(110, 240),
        steps=[("setup", "cargo fetch --locked"), ("lint", "cargo fmt --check && cargo clippy -- -D warnings"),
               ("test", "cargo nextest run && cargo audit"), ("build", "cargo build --release --locked")],
        tools="cargo nextest, clippy, rustfmt, cargo-audit, proptest, criterion",
        gotcha="Builds are slow. Use sccache and cargo-chef layers in Docker."),
    "web": dict(
        label="Web (TypeScript)", image="node:24-slim + Playwright browsers", pkg="npm", secs=(80, 170),
        steps=[("setup", "npm ci"), ("lint", "eslint . && tsc --noEmit"),
               ("test", "vitest run && playwright test   # unit + browser tests"),
               ("build", "vite build && lhci autorun   # Lighthouse budget")],
        tools="Vite, Vitest, Playwright, ESLint, axe-core, Lighthouse CI, OWASP ZAP baseline",
        gotcha="Bake Playwright's browsers into the CI image. Retry browser tests once and record a trace, then fix the flaky ones."),
}
SHARED_STEPS = [("secrets", "gitleaks detect --redact"), ("sast", "opengrep scan --config policies/sast")]


def _cloud_cmds(folder, env, login):
    d = "infra/live/%s/%s" % (folder, env)
    return ["tofu -chdir=%s init" % d, "tofu -chdir=%s plan -out plan.bin" % d, "tofu -chdir=%s apply plan.bin" % d, login,
            "helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace -f platform/argocd/values.yaml",
            "kubectl apply -f environments/%s/root-app.yaml" % env]


CLOUDS = [
    dict(short="aks", cloud="Azure", folder="azure", cpu="amd64, AVX-512", factor=1.05,
         login="az aks get-credentials -g rg-factory-{env} -n aks-factory-{env} && kubelogin convert-kubeconfig -l azurecli",
         note="kubectl needs kubelogin. Pods reach Azure through Workload Identity (Entra federated credentials)."),
    dict(short="gke", cloud="Google Cloud", folder="gcp", cpu="amd64, AMX", factor=0.97,
         login="gcloud container clusters get-credentials gke-factory-{env} --region europe-west4",
         note="kubectl needs gke-gcloud-auth-plugin. Pods use Workload Identity Federation. Autopilot restricts privileged DaemonSets."),
    dict(short="eks", cloud="AWS", folder="aws", cpu="arm64, Graviton", factor=1.01,
         login="aws eks update-kubeconfig --name eks-factory-{env} --region eu-west-1",
         note="Access entries replace the old aws-auth ConfigMap. Pods use EKS Pod Identity. arm64 nodes match Apple Silicon and cost less."),
]

TARGETS = [
    dict(id="mac-kind", env="local", cloud="macOS", where="kind on Colima, on the developer's laptop", cpu="arm64, Apple Silicon", factor=0.9,
         cmds=["brew bundle --file Brewfile", "mise install", "colima start --cpu 4 --memory 8",
               "kind create cluster --name factory --config local/kind.yaml", "tilt up"],
         note="Same manifests as the clouds, but no real load balancer, storage classes or IAM. Force device='cpu' so tests skip MPS."),
    dict(id="docker-dev", env="dev", cloud="Docker", where="Docker Compose on the shared dev host", cpu="amd64", factor=1.0,
         cmds=["ansible-playbook -i ansible/inventories/dev ansible/docker_host.yml",
               "docker compose -p factory -f deploy/compose.yaml up -d --wait"],
         note="Fast feedback without Kubernetes. Good for service tests, not for rollout or scaling tests."),
] + [
    dict(id="%s-%s" % (c["short"], env), env=env, cloud=c["cloud"], cpu=c["cpu"], factor=c["factor"], note=c["note"],
         where="%s, Kubernetes 1.35, 3 general nodes, CPU only" % c["short"].upper(),
         cmds=_cloud_cmds(c["folder"], env, c["login"].format(env=env)))
    for env in ("staging", "prod") for c in CLOUDS
]

# Model gates. A candidate must pass every one to move down the line.
GATES = [
    dict(suite="Quality", metric="f1_macro", op=">=", limit=0.88, tool="pytest golden set, MLflow evaluate",
         why="Score on a held-out golden set the model never trained on."),
    dict(suite="Regression", metric="delta_f1", op=">=", limit=-0.01, tool="compare with the champion",
         why="A new model may not be meaningfully worse than the one in production."),
    dict(suite="Robustness", metric="f1_perturbed", op=">=", limit=0.80, tool="typo and paraphrase perturbations",
         why="Score when the input has typos, slang and rephrasing."),
    dict(suite="Fairness", metric="subgroup_gap", op="<=", limit=0.05, tool="Fairlearn",
         why="Largest score gap between customer groups."),
    dict(suite="Safety", metric="safety_pass", op=">=", limit=0.95, tool="garak and Inspect probes",
         why="Share of adversarial and prompt-injection probes handled correctly."),
    dict(suite="Speed", metric="p95_ms", op="<=", limit=120, tool="k6 on a 2-CPU reference pod",
         why="95th percentile latency of the int8 ONNX file on CPU."),
    dict(suite="Data", metric="drift", op="<=", limit=0.20, tool="Evidently, Great Expectations",
         why="Schema is valid and evaluation data still looks like training data."),
]
CANARY_LIMITS = dict(p95_ms=120, error_rate=1.0)

MODEL_STORY = [
    dict(tag="v1", by="sam", data=("support-tickets", "1.0", 48000, "First labelled export"), why="Baseline.",
         params=dict(base="MiniLM-L6, 22M params", epochs=3, lr="3e-5", export="ONNX int8, 1 thread per CPU"),
         metrics=dict(f1_macro=0.902, f1_perturbed=0.841, subgroup_gap=0.031, safety_pass=0.970, p95_ms=84, drift=0.08),
         size_mb=24, canary=[(86, 0.2), (88, 0.3), (87, 0.2)]),
    dict(tag="v2", by="sam", data=("support-tickets", "1.1", 61000, "Adds chat transcripts"), why="Bigger model for better quality.",
         params=dict(base="MiniLM-L12, 33M params", epochs=4, lr="2e-5", export="ONNX int8, 1 thread per CPU"),
         metrics=dict(f1_macro=0.921, f1_perturbed=0.863, subgroup_gap=0.036, safety_pass=0.971, p95_ms=106, drift=0.09),
         size_mb=35, canary=[(171, 2.4)]),
    dict(tag="v3", by="lea", data=("support-tickets", "1.1", 61000, "Adds chat transcripts"), why="Distil v2 back into the small architecture.",
         params=dict(base="MiniLM-L6 distilled from v2", epochs=5, lr="3e-5", export="ONNX int8, 1 thread per CPU"),
         metrics=dict(f1_macro=0.917, f1_perturbed=0.852, subgroup_gap=0.088, safety_pass=0.968, p95_ms=79, drift=0.10),
         size_mb=24, canary=[(81, 0.2), (82, 0.2), (80, 0.2)]),
    dict(tag="v4", by="lea", data=("support-tickets", "1.2", 66000, "Rebalanced across customer groups"), why="Same recipe as v3 on rebalanced data.",
         params=dict(base="MiniLM-L6 distilled from v2", epochs=5, lr="3e-5", export="ONNX int8, 1 thread per CPU"),
         metrics=dict(f1_macro=0.919, f1_perturbed=0.861, subgroup_gap=0.034, safety_pass=0.972, p95_ms=81, drift=0.07),
         size_mb=24, canary=[(83, 0.2), (84, 0.2), (82, 0.2)]),
]

ADRS = [
    ("ADR-001", "Git is the source of truth for code, policy, access and deployments", "accepted",
     "Every change is a pull request, so every change has an author, a reviewer and an undo."),
    ("ADR-002", "OpenTofu instead of Terraform", "accepted",
     "Terraform's BSL licence is not open source. OpenTofu runs the same code."),
    ("ADR-003", "One pipeline contract for every language", "accepted",
     "Each repo offers make setup, lint, test and build. CI only calls make, so a Mac and CI behave the same."),
    ("ADR-004", "Build once, promote by digest", "accepted",
     "The image tested in staging is byte for byte the image in production."),
    ("ADR-005", "Keycloak groups drive every tool's roles", "accepted",
     "Access is one YAML file. Onboarding is a pull request and offboarding is one script."),
    ("ADR-006", "Model gates live in Git", "accepted",
     "Thresholds change by reviewed pull request, never by editing a dashboard."),
    ("ADR-007", "One Argo CD per cluster, pulling from Git", "accepted",
     "No central hub holds credentials for every cloud."),
    ("ADR-008", "CPU only, small models, shipped inside the image", "accepted",
     "One digest rolls back code and model together. No GPU pools, drivers or quota to manage."),
]


# --------------------------------------------------------------------------
# Shared context
# --------------------------------------------------------------------------

class AccessDenied(Exception):
    pass


def paint(text, code):
    return "\033[%sm%s\033[0m" % (code, text) if sys.stdout.isatty() else text


class Sim:
    """Clock, random numbers, audit log and chat feed shared by every station."""

    def __init__(self, seed=42, quiet=False):
        self.rng = random.Random(seed)
        self.now = datetime(2026, 9, 14, 8, 30, tzinfo=timezone.utc)   # a Monday
        self.audit, self.chat, self.quiet = [], [], quiet

    def stamp(self):
        return self.now.strftime("%a %H:%M")

    def next_day(self):
        self.now = (self.now + timedelta(days=1)).replace(hour=8, minute=30)

    def phase(self, title):
        if not self.quiet:
            print("\n" + paint(title, "1"))

    def log(self, tool, actor, action, target, result="ok", detail=""):
        self.now += timedelta(minutes=self.rng.randint(1, 5))
        entry = dict(n=len(self.audit) + 1, t=self.stamp(), tool=tool, actor=actor, action=action,
                     target=target, result=result, detail=detail)
        self.audit.append(entry)
        if not self.quiet:
            mark = paint(result, "32" if result in ("ok", "passed") else "31" if result in ("denied", "failed", "blocked", "aborted") else "33")
            print("  %s  %-9s %-11s %-13s %-40s %s  %s" % (entry["t"], tool, actor, action, target[:40], mark, detail[:70]))
        return entry

    def say(self, channel, text):
        self.chat.append(dict(t=self.stamp(), channel=channel, text=text))

    def digest(self, *parts, n=12):
        return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:n]


# --------------------------------------------------------------------------
# Stations. Each one stands in for a real tool.
# --------------------------------------------------------------------------

class Identity:
    """Keycloak stand-in: users, groups, tokens, and the permission check every station calls."""
    tool = "keycloak"

    def __init__(self, sim):
        self.sim = sim
        self.users = {u["id"]: dict(u, active=True, bot=u.get("bot", False)) for u in USERS}
        self.sessions, self.denials = [], []

    def ensure(self, uid):
        """Single sign-on: one login, one token, accepted by every tool."""
        if any(s["user"] == uid for s in self.sessions):
            return
        u = self.users[uid]
        if not u["active"]:
            self.require(uid, "login", "realm factory", self.tool, "account disabled")
        groups = ["team-" + u["team"], "role-" + u["role"]]
        e = self.sim.log(self.tool, uid, "login", "realm factory", "ok", "OIDC token, groups: " + ", ".join(groups))
        self.sessions.append(dict(user=uid, t=e["t"], groups=groups, how="device flow" if not u["bot"] else "client credentials"))

    def can(self, uid, perm):
        u = self.users.get(uid)
        if not u or not u["active"]:
            return False
        perms = ROLES[u["role"]]["perms"]
        return "*" in perms or perm in perms

    def require(self, uid, perm, target, tool, reason=""):
        if not reason and self.can(uid, perm):
            return
        role = self.users[uid]["role"]
        why = reason or "role %s lacks %s" % (role, perm)
        e = self.sim.log(tool, uid, perm, target, "denied", why)
        self.denials.append(dict(t=e["t"], user=uid, role=role, tool=tool, wanted=perm, target=target, why=why))
        raise AccessDenied(why)

    def maintainer_of(self, team):
        return next(u["id"] for u in self.users.values() if u["team"] == team and u["role"] == "maintainer")

    def offboard(self, uid, by):
        self.require(by, "access:manage", uid, self.tool)
        self.users[uid]["active"] = False
        self.sessions = [s for s in self.sessions if s["user"] != uid]
        for tool, what in [("keycloak", "disable account, end sessions"), ("forgejo", "delete SSH keys and personal tokens"),
                           ("harbor", "revoke CLI secret"), ("mlflow", "remove experiment permissions"),
                           ("argocd", "revoke API tokens"), ("clouds", "remove federation bindings in all three")]:
            self.sim.log(tool, by, "offboard", uid, "ok", what)


class Forge:
    """Forgejo stand-in: commits, pull requests, branch protection, tags."""
    tool = "forgejo"

    def __init__(self, sim, idp):
        self.sim, self.idp = sim, idp
        self.repos = {r["name"]: dict(r, commits=[], prs=[], tags=[]) for r in REPOS}

    def _add(self, repo, author, message, branch):
        r = self.repos[repo]
        sha = self.sim.digest(repo, author, message, len(r["commits"]), n=8)
        e = self.sim.log(self.tool, author, "push", "%s@%s" % (repo, branch), "ok", "%s %s" % (sha, message))
        r["commits"].append(dict(sha=sha, author=author, message=message, branch=branch, t=e["t"]))
        return sha

    def commit(self, repo, author, message, branch):
        self.idp.require(author, "repo:write", repo, self.tool)
        return self._add(repo, author, message, branch)

    def open_pr(self, repo, author, title, branch, sha):
        r = self.repos[repo]
        pr = dict(id=len(r["prs"]) + 1, repo=repo, title=title, author=author, branch=branch, head=sha,
                  approvals=[], ci="pending", status="open")
        r["prs"].append(pr)
        self.sim.log(self.tool, author, "open PR", "%s#%d" % (repo, pr["id"]), "ok", title)
        return pr

    def approve(self, pr, reviewer):
        ref = "%s#%d" % (pr["repo"], pr["id"])
        self.idp.require(reviewer, "pr:review", ref, self.tool)
        pr["approvals"].append(reviewer)
        self.sim.log(self.tool, reviewer, "approve", ref)

    def merge(self, pr, user):
        ref = "%s#%d" % (pr["repo"], pr["id"])
        self.idp.require(user, "pr:merge", ref, self.tool)
        if not [a for a in pr["approvals"] if a != pr["author"]]:
            self.idp.require(user, "pr:merge", ref, self.tool, "branch protection: needs one approval from someone else")
        if pr["ci"] != "passed":
            self.idp.require(user, "pr:merge", ref, self.tool, "branch protection: CI is not green")
        pr["status"] = "merged"
        return self._add(pr["repo"], user, "Merge #%d: %s" % (pr["id"], pr["title"]), "main")

    def next_version(self, repo):
        return "1.0.%d" % len(self.repos[repo]["tags"])

    def tag(self, repo, sha, version):
        self.repos[repo]["tags"].append(dict(name=version, sha=sha, t=self.sim.stamp()))


class Registry:
    """Harbor stand-in: images with digest, SBOM, scan result, signature, replication. Packages too."""
    tool = "harbor"

    def __init__(self, sim, idp):
        self.sim, self.idp = sim, idp
        self.images, self.packages = [], []

    def build(self, repo, sha, version, critical):
        self.idp.require("bot-ci", "artifact:push", repo, self.tool)
        rng = self.sim.rng
        blocked = critical > 0
        img = dict(repo=repo, tag=version, git=sha, digest="sha256:" + self.sim.digest(repo, sha, version, n=16),
                   arch="amd64 + arm64", size_mb=rng.randint(38, 180), sbom=rng.randint(60, 420),
                   vulns=dict(critical=critical, high=rng.randint(0, 3), medium=rng.randint(2, 11)),
                   signed=not blocked, status="blocked" if blocked else "pushed",
                   replicated="none" if blocked else "ACR, Artifact Registry, ECR")
        e = self.sim.log(self.tool, "bot-ci", "push image", "%s:%s" % (repo, version), img["status"],
                         "critical CVE with a fix available: policy blocks the push" if blocked else "signed %s" % img["digest"][:19])
        img["t"] = e["t"]
        self.images.append(img)
        return img

    def publish(self, repo, kind, version):
        self.packages.append(dict(name=repo, type=kind, version=version, t=self.sim.stamp()))


class CI:
    """CI runner stand-in. Runs each language's make targets, then the shared checks, then the release steps."""
    tool = "ci"

    def __init__(self, sim, idp, forge, registry):
        self.sim, self.idp, self.forge, self.registry = sim, idp, forge, registry
        self.pipelines = []

    def run(self, repo, sha, branch, fail=None, flaky=None):
        self.idp.require("bot-ci", "ci:run", repo, self.tool)
        lang = self.forge.repos[repo]["lang"]
        tc, rng, steps, status = TOOLCHAINS[lang], self.sim.rng, [], "passed"
        for name, cmd in tc["steps"] + SHARED_STEPS:
            if status == "failed":
                steps.append(dict(name=name, cmd=cmd, status="skipped", secs=0, note=""))
                continue
            step = dict(name=name, cmd=cmd, status="passed", note="",
                        secs=rng.randint(*tc["secs"]) if name in ("test", "build") else rng.randint(6, 35))
            if fail and fail[0] == name:
                step.update(status="failed", note=fail[1])
                status = "failed"
            elif flaky and flaky[0] == name:
                step.update(status="flaky", note=flaky[1])
            steps.append(step)
        p = dict(id=len(self.pipelines) + 1, repo=repo, lang=tc["label"], image=tc["image"], sha=sha, branch=branch,
                 status=status, steps=steps, coverage=round(rng.uniform(81, 94), 1))
        bad = [s for s in steps if s["status"] in ("failed", "flaky")]
        e = self.sim.log(self.tool, "bot-ci", "pipeline", "%s@%s" % (repo, sha), status,
                         "%s: %s" % (bad[0]["name"], bad[0]["note"]) if bad else "coverage %.1f%%" % p["coverage"])
        p["t"] = e["t"]
        self.pipelines.append(p)
        return p

    def release(self, p, version, critical=0):
        """Main branch only. Libraries publish a package; everything else also ships a signed multi-arch image."""
        repo, r = p["repo"], self.forge.repos[p["repo"]]
        pkg = TOOLCHAINS[r["lang"]]["pkg"]
        img = None
        if r["kind"] != "library":
            img = self.registry.build(repo, p["sha"], version, critical)
            ref = "harbor.factory.example/%s/%s" % (r["team"], repo)
            blocked = img["status"] == "blocked"
            for name, cmd in [("image", "docker buildx build --platform linux/amd64,linux/arm64 -t %s:%s ." % (ref, version)),
                              ("sbom", "syft %s:%s -o spdx-json > sbom.json" % (ref, version)),
                              ("scan", "grype sbom:sbom.json --fail-on critical --only-fixed"),
                              ("sign", "cosign sign %s@%s" % (ref, img["digest"][:19]))]:
                st = "failed" if blocked and name == "scan" else "skipped" if blocked and name == "sign" else "passed"
                note = "1 critical CVE in the base image, fix available" if st == "failed" else ""
                p["steps"].append(dict(name=name, cmd=cmd, status=st, secs=self.sim.rng.randint(8, 60), note=note))
            if blocked:
                p["status"] = "blocked"
                return img
        p["steps"].append(dict(name="package", cmd="publish %s to the forge's %s registry" % (version, pkg), status="passed",
                               secs=self.sim.rng.randint(5, 20), note=""))
        self.registry.publish(repo, pkg, version)
        return img


class ModelHub:
    """DVC + MLflow + the evaluation harness, in one stand-in."""
    tool = "mlflow"

    def __init__(self, sim, idp):
        self.sim, self.idp = sim, idp
        self.datasets, self.runs, self.versions, self.speed_checks = [], [], [], []
        self.champion = None

    def dataset(self, name, version, rows, note, actor):
        found = [d for d in self.datasets if (d["name"], d["version"]) == (name, version)]
        if found:
            return found[0]
        self.idp.require(actor, "data:write", name, "dvc")
        d = dict(name=name, version=version, rows=rows, note=note, by=actor, hash="md5:" + self.sim.digest(name, version, rows))
        e = self.sim.log("dvc", actor, "dvc push", "%s:%s" % (name, version), "ok", "%d rows, %s" % (rows, d["hash"]))
        d["t"] = e["t"]
        self.datasets.append(d)
        return d

    def train(self, spec, data, git_sha, actor):
        self.idp.require(actor, "model:train", MODEL, self.tool)
        rng, base = self.sim.rng, spec["metrics"]
        wobble = dict(f1_macro=0.003, f1_perturbed=0.004, subgroup_gap=0.003, safety_pass=0.004, p95_ms=3, drift=0.01)
        m = {k: round(v + rng.uniform(-wobble[k], wobble[k]), 3) for k, v in base.items()}
        m["p95_ms"] = round(m["p95_ms"])
        champ = self.champion and self.version(self.champion)["metrics"]["f1_macro"]
        m["delta_f1"] = round(m["f1_macro"] - champ, 3) if champ else 0.0
        run = dict(run_id=self.sim.digest(MODEL, spec["tag"], git_sha, n=10), tag=spec["tag"], why=spec["why"],
                   dataset="%s:%s" % (data["name"], data["version"]), data_hash=data["hash"], git=git_sha,
                   params=spec["params"], metrics=m, size_mb=spec["size_mb"], by=actor, minutes=rng.randint(22, 48))
        e = self.sim.log(self.tool, actor, "train on CPU", "%s %s" % (MODEL, spec["tag"]), "ok",
                         "run %s, f1 %.3f, %d min on 8 vCPU" % (run["run_id"], m["f1_macro"], run["minutes"]))
        run["t"] = e["t"]
        self.runs.append(run)
        return run

    def evaluate_and_register(self, run):
        self.idp.require("bot-ci", "model:register", MODEL, self.tool)
        results = []
        for g in GATES:
            v = run["metrics"][g["metric"]]
            ok = v >= g["limit"] if g["op"] == ">=" else v <= g["limit"]
            results.append(dict(suite=g["suite"], metric=g["metric"], value=v, op=g["op"], limit=g["limit"], passed=ok))
        failed = [r["suite"] for r in results if not r["passed"]]
        self.sim.log("evals", "bot-ci", "gate check", "%s %s" % (MODEL, run["tag"]), "failed" if failed else "passed",
                     "stopped by: " + ", ".join(failed) if failed else "all %d gates passed" % len(GATES))
        ver = dict(version=run["tag"], run_id=run["run_id"], status="rejected" if failed else "candidate", gates=results,
                   metrics=run["metrics"], size_mb=run["size_mb"], format="ONNX int8", by=run["by"], note="",
                   lineage=dict(git=run["git"], data=run["data_hash"], dataset=run["dataset"],
                                artifact="sha256:" + self.sim.digest(MODEL, run["run_id"], n=16)))
        e = self.sim.log(self.tool, "bot-ci", "register", "%s %s" % (MODEL, run["tag"]), "ok", "status " + ver["status"])
        ver["t"] = e["t"]
        self.versions.append(ver)
        return ver

    def version(self, tag):
        return next(v for v in self.versions if v["version"] == tag)

    def speed_check(self, ver, target):
        """Chips differ per cloud, so the speed gate runs again on every staging cluster."""
        ms = round(ver["metrics"]["p95_ms"] * target["factor"] + self.sim.rng.uniform(-2, 2))
        ok = ms <= CANARY_LIMITS["p95_ms"]
        self.sim.log("evals", "bot-ci", "speed check", "%s %s on %s" % (MODEL, ver["version"], target["id"]),
                     "passed" if ok else "failed", "p95 %d ms on %s (limit %d)" % (ms, target["cpu"], CANARY_LIMITS["p95_ms"]))
        self.speed_checks.append(dict(version=ver["version"], target=target["id"], cpu=target["cpu"], p95_ms=ms, passed=ok))
        return ok

    def promote(self, ver, actor):
        ref = "%s %s -> champion" % (MODEL, ver["version"])
        self.idp.require(actor, "model:promote", ref, self.tool)
        if ver["status"] == "rejected":
            self.idp.require(actor, "model:promote", ref, self.tool, "gates failed: a rejected version cannot be promoted")
        if self.champion:
            self.version(self.champion)["status"] = "previous"
        ver["status"], self.champion = "champion", ver["version"]
        self.sim.log(self.tool, actor, "set alias", ref)


class Infra:
    """OpenTofu, Ansible and the cloud CLIs. Records the commands a real run would execute."""

    def __init__(self, sim, idp):
        self.sim, self.idp, self.state = sim, idp, {}

    def provision(self, target, actor):
        tool = "ansible" if target["cloud"] in ("macOS", "Docker") else "opentofu"
        self.idp.require(actor, "infra:apply", target["id"], tool)
        e = self.sim.log(tool, actor, "apply", target["id"], "ok", target["cmds"][0])
        self.state[target["id"]] = dict(status="ready", by=actor, t=e["t"], tool=tool)


class Delivery:
    """Argo CD and Argo Rollouts stand-in. Desired state is a commit in the environments repo; rollback is a revert."""
    tool = "argocd"

    def __init__(self, sim, idp):
        self.sim, self.idp = sim, idp
        self.live = {t["id"]: {} for t in TARGETS}
        self.env_commits, self.history, self.rollouts = [], [], []

    def _set(self, app, version, digest, target, actor, kind="deploy"):
        prev = self.live[target["id"]].get(app, {}).get("version")
        sha = self.sim.digest(app, version, target["id"], len(self.env_commits), n=8)
        verb = "revert" if kind == "rollback" else "sync"
        e = self.sim.log(self.tool, actor, verb, "%s %s -> %s" % (app, version, target["id"]), "ok", "environments@%s, %s" % (sha, digest[:19]))
        change = "%s -> %s" % (prev or "none", version)
        self.env_commits.append(dict(sha=sha, path="environments/%s/%s/%s.yaml" % (target["env"], target["id"], app),
                                     change=("revert: " if kind == "rollback" else "") + change, by=actor, t=e["t"]))
        self.live[target["id"]][app] = dict(version=version, digest=digest, health="Healthy", sync="Synced", since=e["t"])
        self.history.append(dict(t=e["t"], app=app, target=target["id"], env=target["env"], kind=kind, change=change, by=actor, commit=sha))

    def deploy(self, app, version, digest, env, actor, skip=()):
        self.idp.require(actor, "deploy:" + env, "%s %s -> %s" % (app, version, env), self.tool)
        for t in TARGETS:
            if t["env"] == env and t["id"] not in skip:
                self._set(app, version, digest, t, actor)

    def canary(self, app, version, digest, target_id, actor, observed):
        """10% -> 50% -> 100%, with an automatic analysis after each step. A failed analysis aborts and reverts."""
        self.idp.require(actor, "deploy:prod", "%s %s -> %s" % (app, version, target_id), self.tool)
        target = next(t for t in TARGETS if t["id"] == target_id)
        prev, steps, rng = self.live[target_id].get(app), [], self.sim.rng
        for weight, (p95, err) in zip((10, 50, 100), observed):
            p95, err = round(p95 + rng.uniform(-2, 2)), round(err + rng.uniform(-0.05, 0.05), 2)
            ok = p95 <= CANARY_LIMITS["p95_ms"] and err <= CANARY_LIMITS["error_rate"]
            e = self.sim.log("rollouts", "bot-gitops", "canary %d%%" % weight, "%s %s on %s" % (app, version, target_id),
                             "passed" if ok else "aborted", "p95 %d ms, errors %.2f%%" % (p95, err))
            steps.append(dict(weight=weight, p95_ms=p95, error_rate=err, passed=ok, t=e["t"]))
            if not ok:
                break
        good = all(s["passed"] for s in steps)
        rollout = dict(app=app, version=version, target=target_id, approved_by=actor, steps=steps,
                       result="promoted" if good else "aborted", failed_at=None if good else self.sim.now)
        self.rollouts.append(rollout)
        if good:
            self._set(app, version, digest, target, actor)
        elif prev:
            self._set(app, prev["version"], prev["digest"], target, "argo-rollouts", kind="rollback")
            rollout["restored_minutes"] = int((self.sim.now - rollout["failed_at"]).total_seconds() // 60)
        rollout.pop("failed_at")
        return good


# --------------------------------------------------------------------------
# The scenario: one simulated week on the factory floor
# --------------------------------------------------------------------------

class Factory:
    def __init__(self, seed, quiet):
        self.sim = Sim(seed, quiet)
        self.idp = Identity(self.sim)
        self.forge = Forge(self.sim, self.idp)
        self.registry = Registry(self.sim, self.idp)
        self.ci = CI(self.sim, self.idp, self.forge, self.registry)
        self.hub = ModelHub(self.sim, self.idp)
        self.infra = Infra(self.sim, self.idp)
        self.delivery = Delivery(self.sim, self.idp)
        self.adrs = [dict(id=a, title=b, status=c, why=d) for a, b, c, d in ADRS]
        self.alerts, self.lead_hours, self.prod_changes, self.prod_failures = [], [], 0, 0

    def attempt(self, what, *args):
        """Run something we expect policy to refuse, and carry on."""
        try:
            what(*args)
        except AccessDenied:
            pass

    def ship(self, repo, author, reviewer, message, fail=None, flaky=None, cve=False, try_self_merge=False):
        """One change through the code half of the line: branch, PR, CI, review, merge, release, deploy up to staging."""
        sim, forge = self.sim, self.forge
        started = sim.now
        for u in (author, reviewer):
            self.idp.ensure(u)
        branch = "feat/" + "-".join(message.lower().split()[:3])
        sha = forge.commit(repo, author, message, branch)
        pr = forge.open_pr(repo, author, message, branch, sha)
        p = self.ci.run(repo, sha, branch, fail=fail, flaky=flaky)
        if p["status"] == "failed":
            sim.say("#" + forge.repos[repo]["team"], "%s: CI caught '%s' before review. %s pushed a fix." % (repo, fail[1], author))
            pr["head"] = sha = forge.commit(repo, author, fail[2], branch)
            p = self.ci.run(repo, sha, branch)
        if flaky:
            sim.say("#" + forge.repos[repo]["team"], "%s: a browser test passed only on retry. Logged as flaky with a trace attached." % repo)
        pr["ci"] = p["status"]
        if try_self_merge:
            self.attempt(forge.merge, pr, author)
        forge.approve(pr, reviewer)
        main = forge.merge(pr, author)
        version = forge.next_version(repo)
        p = self.ci.run(repo, main, "main")
        img = self.ci.release(p, version, critical=1 if cve else 0)
        forge.tag(repo, main, version)
        if img and img["status"] == "blocked":
            sim.say("#security", "%s %s blocked: critical CVE in the base image. Nothing was pushed." % (repo, version))
            return dict(self.ship(repo, author, reviewer, "Bump base image to the patched release"), started=started)
        if forge.repos[repo]["kind"] in DEPLOYABLE:
            self.delivery.deploy(repo, version, img["digest"], "local", author)
            for env in ("dev", "staging"):
                self.delivery.deploy(repo, version, img["digest"], env, "bot-gitops")
        return dict(repo=repo, version=version, image=img, sha=main, started=started)

    def to_prod(self, shipped):
        owner = self.idp.maintainer_of(self.forge.repos[shipped["repo"]]["team"])
        self.idp.ensure(owner)
        self.delivery.deploy(shipped["repo"], shipped["version"], shipped["image"]["digest"], "prod", owner)
        self.prod_changes += 1
        self.lead_hours.append((self.sim.now - shipped["started"]).total_seconds() / 3600)

    def model_cycle(self, spec, trainer_sha, lead):
        """The model half of the line: data, train, gates, register, staging on three clouds, canary, champion."""
        sim, hub = self.sim, self.hub
        started = sim.now
        self.idp.ensure(spec["by"])
        data = hub.dataset(*spec["data"], actor=spec["by"])
        run = hub.train(spec, data, trainer_sha, spec["by"])
        ver = hub.evaluate_and_register(run)
        if ver["status"] == "rejected":
            failed = [g for g in ver["gates"] if not g["passed"]][0]
            ver["note"] = "Stopped at the %s gate: %s %s, limit %s." % (failed["suite"], failed["metric"], failed["value"], failed["limit"])
            sim.say("#nlp", "%s %s stopped at the %s gate (%s = %s, limit %s). It never left the registry." %
                    (MODEL, ver["version"], failed["suite"], failed["metric"], failed["value"], failed["limit"]))
            return ver
        artifact = ver["lineage"]["artifact"]
        self.delivery.deploy(MODEL, ver["version"], artifact, "staging", "bot-gitops")
        slow = [t["id"] for t in TARGETS if t["env"] == "staging" and not hub.speed_check(ver, t)]
        if slow:
            ver["status"], ver["note"] = "rejected", "Too slow on %s in staging." % ", ".join(slow)
            return ver
        self.idp.ensure(lead)
        self.prod_changes += 1
        if self.delivery.canary(MODEL, ver["version"], artifact, "eks-prod", lead, spec["canary"]):
            self.delivery.deploy(MODEL, ver["version"], artifact, "prod", lead, skip=("eks-prod",))
            hub.promote(ver, lead)
            self.lead_hours.append((sim.now - started).total_seconds() / 3600)
            sim.say("#releases", "%s %s is the new champion on AKS, GKE and EKS." % (MODEL, ver["version"]))
        else:
            self.prod_failures += 1
            rollout = self.delivery.rollouts[-1]
            bad = rollout["steps"][-1]
            ver["status"] = "rolled back"
            ver["note"] = "Passed every offline gate, then failed the production canary under real concurrency."
            self.alerts.append(dict(t=bad["t"], name="ModelLatencyHigh", severity="critical", target="eks-prod", status="resolved",
                                    detail="p95 %d ms and %.1f%% errors during the %s canary. Rolled back automatically in %d minutes." %
                                           (bad["p95_ms"], bad["error_rate"], ver["version"], rollout["restored_minutes"])))
            sim.say("#releases", "%s %s canary aborted on eks-prod at 10%% traffic. Argo Rollouts reverted to %s. No one was paged twice." %
                    (MODEL, ver["version"], self.hub.champion))
            self.adrs.append(dict(id="ADR-009", title="The speed gate replays production traffic", status="accepted after the v2 rollback",
                                  why="A one-request-at-a-time latency test passed a model that failed under real concurrency on 2-CPU pods."))
            sim.say("#nlp", "Gate change merged: Speed now replays 40 requests per second with the production thread settings.")
        return ver

    def play(self):
        sim, idp = self.sim, self.idp

        sim.phase("Monday. The platform team builds the floor.")
        idp.ensure("ana")
        for uid in ("bot-ci", "bot-gitops"):
            idp.ensure(uid)
        for t in TARGETS:
            self.infra.provision(t, "ana")
        sim.say("#platform", "All eight targets are ready: mac-kind, docker-dev, and staging plus prod on AKS, GKE and EKS.")

        sim.phase("Monday to Tuesday. Six repos, six toolchains, one pipeline contract.")
        shipped = [
            self.ship("fast-tokenizer", "lea", "sam", "Add byte-fallback for unknown characters"),
            self.ship("model-trainer", "sam", "lea", "Export int8 ONNX with fixed thread count"),
            self.ship("inference-engine", "tom", "mei", "Batch requests up to 8 per call", try_self_merge=True,
                      fail=("test", "ASan: heap-use-after-free in BatchQueue::pop", "Fix lifetime of batch buffer")),
        ]
        sim.next_day()
        shipped += [
            self.ship("feature-service", "noor", "raj", "Cache customer features for 60 seconds", cve=True),
            self.ship("model-gateway", "raj", "noor", "Route by model version header"),
            self.ship("eval-dashboard", "ben", "zoe", "Show gate results per model version",
                      flaky=("test", "playwright: 'filters by version' passed on retry")),
        ]
        for s in shipped:
            if s["image"] and self.forge.repos[s["repo"]]["kind"] in DEPLOYABLE:
                self.to_prod(s)
        trainer_sha = next(s["sha"] for s in shipped if s["repo"] == "model-trainer")

        sim.next_day()
        sim.phase("Wednesday. The first model goes down the line.")
        self.model_cycle(MODEL_STORY[0], trainer_sha, "lea")

        sim.next_day()
        sim.phase("Thursday. A bigger model passes every offline gate, then fails the canary.")
        self.model_cycle(MODEL_STORY[1], trainer_sha, "lea")

        sim.next_day()
        sim.phase("Friday. One model is stopped by a gate, the next one becomes champion.")
        v3 = self.model_cycle(MODEL_STORY[2], trainer_sha, "lea")
        idp.ensure("noor")
        self.attempt(self.hub.promote, v3, "noor")
        self.attempt(self.hub.promote, v3, "lea")
        self.model_cycle(MODEL_STORY[3], trainer_sha, "lea")

        sim.phase("Friday afternoon. Access checks and an offboarding.")
        idp.ensure("kai")
        champ = self.hub.version(self.hub.champion)
        self.attempt(self.delivery.deploy, MODEL, champ["version"], champ["lineage"]["artifact"], "prod", "kai")
        self.attempt(self.infra.provision, TARGETS[-1], "tom")
        idp.offboard("sam", "ana")
        self.attempt(idp.ensure, "sam")
        sim.say("#platform", "sam offboarded: account, SSH keys, tokens and cloud bindings removed in one run of factoryctl offboard.")
        self.alerts.append(dict(t=sim.stamp(), name="InputDriftRising", severity="warning", target="all prod", status="open",
                                detail="Drift score 0.16, limit 0.20. New ticket categories are appearing: plan a data refresh."))
        return self


# --------------------------------------------------------------------------
# Turn station state into one JSON document for the portal
# --------------------------------------------------------------------------

def build_series(f):
    rng, out = f.sim.rng, {}
    for target, base in (("aks-prod", 90), ("gke-prod", 83), ("eks-prod", 86)):
        p95, err = [], []
        for i in range(48):
            v, e = base + rng.uniform(-4, 4) - (5 if i >= 36 else 0), 0.25 + rng.uniform(-0.1, 0.12)
            if target == "eks-prod" and i in (20, 21):
                v, e = 171 - (i - 20) * 14 + rng.uniform(-3, 3), 2.4 - (i - 20) * 0.7
            p95.append(round(v, 1))
            err.append(round(max(e, 0.02), 2))
        marks = ([dict(i=20, label="v2 canary"), dict(i=22, label="rollback")] if target == "eks-prod" else []) + [dict(i=36, label="v4")]
        out[target] = dict(p95_ms=p95, error_rate=err, marks=marks, limit=CANARY_LIMITS["p95_ms"])
    out["drift"] = dict(values=[round(0.07 + i * 0.002 + rng.uniform(-0.008, 0.008), 3) for i in range(48)], limit=0.20)
    return out


def build_state(f, seed):
    repos, pipes, images = list(f.forge.repos.values()), f.ci.pipelines, f.registry.images
    components = []
    for r in repos:
        last = [p for p in pipes if p["repo"] == r["name"]][-1]
        pushed = [i for i in images if i["repo"] == r["name"] and i["status"] == "pushed"]
        components.append(dict(name=r["name"], team=r["team"], lang=TOOLCHAINS[r["lang"]]["label"], kind=r["kind"], about=r["about"],
                               version=r["tags"][-1]["name"], checks=dict(owner=True, ci_green=last["status"] == "passed",
                               coverage=last["coverage"] >= 80, sbom=bool(pushed) or r["kind"] == "library",
                               signed=bool(pushed) or r["kind"] == "library", docs=True)))
    rollbacks = [h for h in f.delivery.history if h["kind"] == "rollback"]
    rejected = [v for v in f.hub.versions if v["status"] == "rejected"]
    blocked = [i for i in images if i["status"] == "blocked"]
    failed = [p for p in pipes if p["status"] != "passed"]
    open_alerts = [a for a in f.alerts if a["status"] == "open"]
    restored = [r["restored_minutes"] for r in f.delivery.rollouts if "restored_minutes" in r]
    days = max((f.sim.now - datetime(2026, 9, 14, 8, 30, tzinfo=timezone.utc)).days + 1, 1)
    line = dict(
        code=("%d commits, %d pull requests" % (sum(len(r["commits"]) for r in repos), sum(len(r["prs"]) for r in repos)), "good"),
        build=("%d pipelines, %d stopped" % (len(pipes), len(failed)), "warn" if failed else "good"),
        scan=("%d images signed, %d blocked" % (len(images) - len(blocked), len(blocked)), "warn" if blocked else "good"),
        train=("%d runs on %d dataset versions" % (len(f.hub.runs), len(f.hub.datasets)), "good"),
        evaluate=("%d of %d versions stopped by a gate" % (len(rejected), len(f.hub.versions)), "warn" if rejected else "good"),
        register=("champion is %s" % f.hub.champion, "good"),
        deploy=("%d syncs, %d rollback" % (len(f.delivery.history) - len(rollbacks), len(rollbacks)), "warn" if rollbacks else "good"),
        observe=("%d open alert%s" % (len(open_alerts), "" if len(open_alerts) == 1 else "s"), "warn" if open_alerts else "good"),
    )
    return dict(
        meta=dict(seed=seed, events=len(f.sim.audit), start="Mon 14 Sep 2026", end=f.sim.now.strftime("%a %d %b %Y"), model=MODEL),
        line={k: dict(text=v[0], lamp=v[1]) for k, v in line.items()},
        dora=dict(prod_changes=f.prod_changes, per_day=round((f.prod_changes - f.prod_failures) / days, 1),
                  lead_hours=round(sum(f.lead_hours) / len(f.lead_hours), 1),
                  failure_rate=round(100 * f.prod_failures / f.prod_changes), restore_minutes=restored[0] if restored else 0),
        users=list(f.idp.users.values()), roles=ROLES, sessions=f.idp.sessions, denials=f.idp.denials,
        repos=repos, toolchains=TOOLCHAINS, pipelines=pipes, images=images, packages=f.registry.packages,
        datasets=f.hub.datasets, runs=f.hub.runs, versions=f.hub.versions, champion=f.hub.champion, gates=GATES,
        speed_checks=f.hub.speed_checks, canary_limits=CANARY_LIMITS,
        targets=[dict(t, state=f.infra.state.get(t["id"], {})) for t in TARGETS],
        live=f.delivery.live, env_commits=f.delivery.env_commits, history=f.delivery.history, rollouts=f.delivery.rollouts,
        series=build_series(f), alerts=f.alerts, components=components, adrs=f.adrs, chat=f.sim.chat,
        audit=f.sim.audit, catalog=CATALOG,
    )


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def cmd_run(args):
    f = Factory(args.seed, args.quiet).play()
    state = build_state(f, args.seed)
    site = HERE / "site"
    site.mkdir(exist_ok=True)
    payload = json.dumps(state, default=str).replace("</", "<\\/")
    template = (HERE / "portal.template.html").read_text(encoding="utf-8")
    (site / "index.html").write_text(template.replace("__FACTORY_DATA__", payload), encoding="utf-8")
    (site / "factory_state.json").write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    (HERE / "TOOL_OPTIONS.md").write_text(as_markdown(), encoding="utf-8")
    d = state["dora"]
    print("\n%d events. %d production changes, %d%% failed, restored in %d minutes. Champion: %s %s." %
          (len(f.sim.audit), d["prod_changes"], d["failure_rate"], d["restore_minutes"], MODEL, f.hub.champion))
    print("Portal:  %s\nState:   %s\nOptions: %s" % (site / "index.html", site / "factory_state.json", HERE / "TOOL_OPTIONS.md"))


def cmd_serve(args):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE / "site"))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        print("Serving the portal at http://localhost:%d  (Ctrl+C to stop)" % args.port)
        httpd.serve_forever()


def cmd_tools(_args):
    for c in CATALOG:
        print("\n%s\n  pick: %s (%s)" % (paint(c["layer"], "1"), c["pick"], c["licence"]))
        for o in c["options"]:
            print("  - %s\n      + %s\n      - %s" % (o["name"], o["pros"], o["cons"]))
        for g in c["gotchas"]:
            print("  ! " + g)


def main():
    ap = argparse.ArgumentParser(description="AI model testing software factory, simulated.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="play the scenario and write site/index.html")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--quiet", action="store_true", help="do not print the event log")
    run.set_defaults(fn=cmd_run)
    serve = sub.add_parser("serve", help="serve ./site on localhost")
    serve.add_argument("--port", type=int, default=8080)
    serve.set_defaults(fn=cmd_serve)
    sub.add_parser("tools", help="print tool options, pros, cons and gotchas").set_defaults(fn=cmd_tools)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
