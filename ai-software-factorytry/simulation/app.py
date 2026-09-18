#!/usr/bin/env python3
"""Aether Forge — simulated software factory control plane (stdlib only)."""
from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
STATE = ROOT / "data" / "state.json"
STATE.parent.mkdir(parents=True, exist_ok=True)

USERS = {
    "ada": {"password": "forge", "name": "Ada Lovelace", "groups": ["platform"]},
    "linus": {"password": "forge", "name": "Linus Torvalds", "groups": ["developer"]},
    "grace": {"password": "forge", "name": "Grace Hopper", "groups": ["ml-engineer", "developer"]},
    "ken": {"password": "forge", "name": "Ken Thompson", "groups": ["reviewer"]},
}
SESSIONS: dict[str, str] = {}
LOCK = threading.Lock()


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed() -> dict:
    return {
        "packages": [
            {"ecosystem": "apt", "name": "openjdk-21-jdk", "version": "21.0.4", "channel": "proxy"},
            {"ecosystem": "apt", "name": "gcc", "version": "13.2", "channel": "proxy"},
            {"ecosystem": "pypi", "name": "pytest", "version": "8.3.3", "channel": "proxy"},
            {"ecosystem": "pypi", "name": "mlflow", "version": "2.16.2", "channel": "proxy"},
            {"ecosystem": "pypi", "name": "dvc", "version": "3.55.2", "channel": "proxy"},
            {"ecosystem": "pypi", "name": "torch", "version": "2.4.1", "channel": "hosted-wheel"},
            {"ecosystem": "maven", "name": "junit-jupiter", "version": "5.11.0", "channel": "proxy"},
            {"ecosystem": "go", "name": "github.com/stretchr/testify", "version": "v1.9.0", "channel": "proxy"},
            {"ecosystem": "crates", "name": "tokio", "version": "1.40.0", "channel": "proxy"},
            {"ecosystem": "npm", "name": "@playwright/test", "version": "1.47.2", "channel": "proxy"},
            {"ecosystem": "oci", "name": "platform/workbench", "version": "stable", "channel": "harbor"},
            {"ecosystem": "oci", "name": "platform/pipeline-runner", "version": "1.8.0", "channel": "harbor"},
            {"ecosystem": "helm", "name": "kserve", "version": "0.14.1", "channel": "harbor"},
        ],
        "repos": [
            {"name": "platform", "desc": "OpenTofu, Ansible, workbench image, catalog tasks", "default_branch": "main", "commits": 128},
            {"name": "models/fraud-ranker", "desc": "Gradient boosted ranker + pytest eval harness", "default_branch": "main", "commits": 42},
            {"name": "tools/web-contract-harness", "desc": "Custom Playwright contract tests published as a catalog task", "default_branch": "main", "commits": 19},
            {"name": "services/ledger-api", "desc": "Go HTTP service with Testcontainers", "default_branch": "main", "commits": 67},
            {"name": "gitops/clusters", "desc": "Desired state for k3s / AKS / GKE / EKS", "default_branch": "main", "commits": 90},
        ],
        "workspaces": [
            {"id": "ws-ada", "name": "ada-platform", "owner": "ada", "image": "harbor.forge.internal/platform/workbench:stable", "runtime": "coder-k3s", "status": "running", "toolchains": ["java", "c++", "python", "go", "rust", "node"]},
            {"id": "ws-grace", "name": "grace-fraud-ranker", "owner": "grace", "image": "harbor.forge.internal/platform/workbench:stable", "runtime": "colima-podman", "status": "running", "toolchains": ["python", "rust"]},
        ],
        "runs": [],
        "models": [
            {"name": "fraud-ranker", "version": "3", "stage": "Production", "metrics": {"f1": 0.91, "auc": 0.96, "latency_p99_ms": 18}, "digest": "sha256:9f3a1c"},
            {"name": "fraud-ranker", "version": "4-rc", "stage": "Staging", "metrics": {"f1": 0.93, "auc": 0.97, "latency_p99_ms": 21}, "digest": "sha256:aa12b0"},
        ],
        "deployments": [
            {"app": "fraud-ranker", "target": "k3s", "env": "stage", "digest": "sha256:aa12b0", "status": "healthy", "git_sha": "b7c21e4"},
            {"app": "fraud-ranker", "target": "aks", "env": "prod", "digest": "sha256:9f3a1c", "status": "healthy", "git_sha": "91aa002"},
        ],
        "knowledge": [
            {"title": "Golden path: Python model", "team": "platform", "body": "Use template lang-python-ml. Never push weights to Git; DVC + MinIO."},
            {"title": "Mac local loop", "team": "platform", "body": "colima start --cpu 6 --memory 12; forge ws start. Build linux/arm64 and linux/amd64."},
            {"title": "Rollback is a Git revert", "team": "sre", "body": "Argo CD syncs the previous digest. Images are immutable. Do not retag latest."},
        ],
        "audit": [],
        "templates": [
            {"id": "lang-python-ml", "languages": ["python"], "stages": ["fetch", "build", "unit", "eval", "package", "scan", "publish", "stage", "promote"]},
            {"id": "lang-java-svc", "languages": ["java"], "stages": ["fetch", "build", "unit", "integration", "package", "scan", "publish", "stage"]},
            {"id": "lang-cpp-lib", "languages": ["c++"], "stages": ["fetch", "cmake", "googletest", "package", "scan", "publish"]},
            {"id": "lang-go-api", "languages": ["go"], "stages": ["fetch", "build", "gotest", "package", "scan", "publish", "stage"]},
            {"id": "lang-rust-cli", "languages": ["rust"], "stages": ["fetch", "clippy", "test", "package", "scan", "publish"]},
            {"id": "web-frontend", "languages": ["js"], "stages": ["fetch", "lint", "unit", "playwright", "package", "scan", "publish", "stage"]},
            {"id": "custom-test-tool", "languages": ["any"], "stages": ["fetch", "build", "unit", "integration", "package", "publish-task", "stage"]},
        ],
    }


def load_state() -> dict:
    with LOCK:
        if not STATE.exists():
            data = seed()
            STATE.write_text(json.dumps(data, indent=2))
            return data
        return json.loads(STATE.read_text())


def save_state(data: dict) -> None:
    with LOCK:
        STATE.write_text(json.dumps(data, indent=2))


def audit(actor: str, action: str, detail: str) -> None:
    data = load_state()
    data["audit"].insert(0, {"ts": utcnow(), "actor": actor, "action": action, "detail": detail})
    data["audit"] = data["audit"][:80]
    save_state(data)


MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[forge]", self.address_string(), fmt % args)

    def _json(self, payload, code=200):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _user(self):
        token = self.headers.get("X-Forge-Token")
        if not token:
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
        if not token:
            q = parse_qs(urlparse(self.path).query)
            token = (q.get("token") or [None])[0]
        return SESSIONS.get(token or "")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n == 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Forge-Token, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        if path == "/health":
            return self._json({"ok": True, "service": "aether-forge-sim", "time": utcnow()})
        if path == "/api/me":
            user = self._user()
            if not user:
                return self._json({"error": "unauthorized"}, 401)
            rec = USERS[user]
            return self._json({"username": user, "name": rec["name"], "groups": rec["groups"]})
        data = load_state()
        if path == "/api/floor":
            return self._json({
                "stations": [
                    {"id": "sso", "name": "Keycloak SSO", "status": "up"},
                    {"id": "git", "name": "Forgejo", "status": "up", "count": len(data["repos"])},
                    {"id": "pkg", "name": "Nexus + Harbor", "status": "up", "count": len(data["packages"])},
                    {"id": "ws", "name": "Workbenches", "status": "up", "count": len(data["workspaces"])},
                    {"id": "ci", "name": "Pipeline factory", "status": "up", "count": len(data["runs"])},
                    {"id": "ml", "name": "MLflow registry", "status": "up", "count": len(data["models"])},
                    {"id": "ship", "name": "GitOps dock", "status": "up", "count": len(data["deployments"])},
                    {"id": "docs", "name": "Outline + Mattermost", "status": "up", "count": len(data["knowledge"])},
                ],
                "targets": ["docker", "podman", "k3s", "aks", "gke", "eks"],
                "note": "Azure managed Kubernetes is AKS. EKS is AWS.",
            })
        if path == "/api/packages":
            q = (qs.get("q") or [""])[0].lower()
            items = data["packages"]
            if q:
                items = [p for p in items if q in p["name"].lower() or q in p["ecosystem"].lower()]
            return self._json(items)
        routes = {
            "/api/repos": "repos",
            "/api/workspaces": "workspaces",
            "/api/templates": "templates",
            "/api/models": "models",
            "/api/deployments": "deployments",
            "/api/knowledge": "knowledge",
            "/api/audit": "audit",
            "/api/runs": "runs",
        }
        if path in routes:
            return self._json(data[routes[path]])
        return self._static(path)

    def _static(self, path: str):
        if path in ("", "/"):
            path = "/index.html"
        rel = path.lstrip("/")
        file = (STATIC / rel).resolve()
        if not str(file).startswith(str(STATIC.resolve())) or not file.is_file():
            self._json({"error": "not found", "path": path}, 404)
            return
        raw = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(file.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()
        if path == "/api/login":
            user = body.get("username", "")
            rec = USERS.get(user)
            if not rec or rec["password"] != body.get("password"):
                return self._json({"error": "invalid credentials"}, 401)
            token = uuid.uuid4().hex
            SESSIONS[token] = user
            audit(user, "sso.login", "Keycloak simulated session issued")
            return self._json({"token": token, "username": user, "name": rec["name"], "groups": rec["groups"], "issuer": "keycloak://forge/realms/internal"})
        user = self._user() or "anonymous"
        data = load_state()
        if path == "/api/repos":
            repo = {"name": body.get("name") or f"scratch/{uuid.uuid4().hex[:6]}", "desc": body.get("desc") or "Created from factory floor", "default_branch": "main", "commits": 1}
            data["repos"].append(repo)
            save_state(data)
            audit(user, "git.create", repo["name"])
            return self._json(repo, 201)
        if path == "/api/workspaces":
            ws = {
                "id": "ws-" + uuid.uuid4().hex[:6],
                "name": body.get("name") or f"{user}-bench",
                "owner": user,
                "image": "harbor.forge.internal/platform/workbench:stable",
                "runtime": body.get("runtime") or "colima-podman",
                "status": "running",
                "toolchains": ["java", "c++", "python", "go", "rust", "node"],
            }
            data["workspaces"].append(ws)
            save_state(data)
            audit(user, "workspace.start", ws["name"])
            return self._json(ws, 201)
        if path == "/api/knowledge":
            item = {"title": body.get("title") or "Untitled", "team": user, "body": body.get("body") or ""}
            data["knowledge"].insert(0, item)
            save_state(data)
            audit(user, "knowledge.publish", item["title"])
            return self._json(item, 201)
        if path == "/api/pipelines/run":
            template_id = body.get("template") or "lang-python-ml"
            tmpl = next((t for t in data["templates"] if t["id"] == template_id), data["templates"][0])
            run = {
                "id": uuid.uuid4().hex[:10],
                "project": body.get("project") or "models/fraud-ranker",
                "template": tmpl["id"],
                "target": body.get("target") or "k3s",
                "kind": body.get("kind") or "app",
                "actor": user,
                "status": "queued",
                "started": utcnow(),
                "finished": None,
                "digest": None,
                "stages": [{"id": s, "status": "queued", "finished": None} for s in tmpl["stages"]],
            }
            data["runs"].insert(0, run)
            save_state(data)
            audit(user, "pipeline.start", f"{run['project']} via {tmpl['id']} → {run['target']}")
            threading.Thread(target=execute_run, args=(run["id"],), daemon=True).start()
            return self._json(run, 202)
        if path == "/api/deploy":
            digest = body.get("digest")
            if not digest:
                digest = data["runs"][0]["digest"] if data["runs"] and data["runs"][0].get("digest") else "sha256:localdev"
            dep = {"app": body.get("app") or "fraud-ranker", "target": body.get("target") or "k3s", "env": body.get("env") or "stage", "digest": digest, "status": "healthy", "git_sha": "manual"}
            data["deployments"].insert(0, dep)
            save_state(data)
            audit(user, "gitops.sync", f"{dep['app']} {dep['env']} @ {dep['target']} {digest}")
            return self._json(dep, 201)
        if path == "/api/rollback":
            rolled = {"app": body.get("app") or "fraud-ranker", "target": body.get("target") or "aks", "env": body.get("env") or "prod", "digest": "sha256:9f3a1c", "status": "rolled-back", "git_sha": "91aa002"}
            data["deployments"].insert(0, rolled)
            save_state(data)
            audit(user, "gitops.rollback", f"{rolled['app']} on {rolled['target']} → {rolled['digest']}")
            return self._json(rolled)
        self._json({"error": "not found"}, 404)


def execute_run(run_id: str) -> None:
    data = load_state()
    run = next((r for r in data["runs"] if r["id"] == run_id), None)
    if not run:
        return
    for stage in run["stages"]:
        time.sleep(0.35)
        stage["status"] = "passed"
        stage["finished"] = utcnow()
        run["status"] = "running"
        save_state(data)
        data = load_state()
        run = next((r for r in data["runs"] if r["id"] == run_id), run)
    run["status"] = "passed"
    run["finished"] = utcnow()
    digest = "sha256:" + uuid.uuid4().hex[:12]
    run["digest"] = digest
    data["deployments"].insert(0, {"app": run["project"], "target": run.get("target") or "k3s", "env": "stage", "digest": digest, "status": "healthy", "git_sha": run_id[:7]})
    if run.get("kind") == "model":
        data["models"].insert(0, {"name": run["project"], "version": str(int(time.time()) % 1000), "stage": "Staging", "metrics": {"f1": 0.92, "auc": 0.95, "latency_p99_ms": 20}, "digest": digest})
    save_state(data)


def main():
    if not STATE.exists():
        save_state(seed())
    host, port = "0.0.0.0", 8080
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Aether Forge simulation  →  http://127.0.0.1:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
