#!/usr/bin/env python3
"""Small, dependency-free API used to simulate an AI software factory."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


CATALOG = [
    {"category": "Identity", "name": "Keycloak", "purpose": "OIDC/SAML SSO, MFA federation, groups and roles", "tier": "core"},
    {"category": "Source", "name": "Gitea", "purpose": "Git repositories, reviews, protected branches and change history", "tier": "core"},
    {"category": "CI", "name": "Tekton", "purpose": "Container-native build, test, evidence and release pipelines", "tier": "core"},
    {"category": "CD", "name": "Argo CD", "purpose": "GitOps reconciliation, drift detection and rollback", "tier": "core"},
    {"category": "Artifacts", "name": "Harbor", "purpose": "OCI images/artifacts, retention, replication and scanning", "tier": "core"},
    {"category": "Packages", "name": "Nexus OSS", "purpose": "Approved dependency proxies and internal packages", "tier": "core"},
    {"category": "Models", "name": "MLflow", "purpose": "Experiment tracking, metrics, artifacts and model versions", "tier": "model"},
    {"category": "Storage", "name": "MinIO", "purpose": "S3-compatible datasets, model files and test evidence", "tier": "model"},
    {"category": "Secrets", "name": "OpenBao", "purpose": "Short-lived credentials, encryption and audit", "tier": "core"},
    {"category": "Policy", "name": "Kyverno", "purpose": "Admission policy, image verification and policy reports", "tier": "security"},
    {"category": "Supply chain", "name": "Cosign + Syft", "purpose": "Artifact signatures, provenance and SBOMs", "tier": "security"},
    {"category": "Scanning", "name": "Trivy + Grype", "purpose": "Dependency, image, IaC and vulnerability scanning", "tier": "security"},
    {"category": "Observability", "name": "OpenTelemetry stack", "purpose": "Metrics, logs, traces, SLOs and model telemetry", "tier": "operations"},
    {"category": "Portal", "name": "Backstage", "purpose": "Optional component catalog and self-service templates", "tier": "optional"},
]

PROFILES = {
    "python-ai": ["uv sync", "ruff check", "mypy", "pytest", "AI evaluation", "build wheel/image"],
    "java": ["mvn verify", "SpotBugs", "JaCoCo", "dependency scan", "build image"],
    "cpp": ["cmake + ninja", "unit tests", "clang-tidy", "ASan/UBSan", "build image"],
    "go": ["go test", "staticcheck", "govulncheck", "build binary/image"],
    "rust": ["cargo test", "clippy", "cargo audit", "build binary/image"],
    "web": ["pnpm test", "ESLint", "axe", "Playwright", "build static image"],
}

INITIAL_PROJECTS = [
    {"name": "fraud-model", "profile": "python-ai", "owner": "risk-ai", "commit": "a91f0c2", "model": "fraud-score:12"},
    {"name": "model-gateway", "profile": "java", "owner": "platform-api", "commit": "e441b9a", "model": None},
    {"name": "evaluation-ui", "profile": "web", "owner": "ai-quality", "commit": "7bc39df", "model": None},
]

INITIAL_DEPLOYMENTS = [
    {"application": "fraud-model", "environment": "test", "version": "sha256:8f31...a4c2", "previous": "sha256:5a10...9de1", "status": "healthy", "updated": utc_now()},
    {"application": "model-gateway", "environment": "staging", "version": "sha256:b24d...17a0", "previous": "sha256:0f98...c711", "status": "healthy", "updated": utc_now()},
]


class FactoryState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.projects = deepcopy(INITIAL_PROJECTS)
        self.deployments = deepcopy(INITIAL_DEPLOYMENTS)
        self.pipeline_runs: list[dict] = []
        self.audit: list[dict] = [
            {"time": utc_now(), "actor": "platform", "action": "simulator.started", "target": "factory"}
        ]

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "projects": deepcopy(self.projects),
                "deployments": deepcopy(self.deployments),
                "pipelines": deepcopy(self.pipeline_runs),
                "audit": deepcopy(self.audit[-30:]),
            }

    def run_pipeline(self, project: str, profile: str) -> dict:
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile: {profile}")
        if not project or len(project) > 80:
            raise ValueError("Project must be between 1 and 80 characters")
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        stages = []
        for index, command in enumerate(PROFILES[profile], start=1):
            stages.append({"order": index, "name": command, "status": "passed", "duration_seconds": index + 1})
        run = {
            "id": run_id,
            "project": project,
            "profile": profile,
            "status": "passed",
            "artifact": f"registry.local/{project}@sha256:{uuid.uuid4().hex}",
            "sbom": "SPDX-2.3",
            "signed": True,
            "started": utc_now(),
            "stages": stages,
        }
        with self.lock:
            self.pipeline_runs.insert(0, run)
            self.pipeline_runs = self.pipeline_runs[:20]
            self.audit.append({"time": utc_now(), "actor": "demo-developer", "action": "pipeline.completed", "target": run_id})
        return deepcopy(run)

    def promote(self, application: str, environment: str, version: str) -> dict:
        allowed_envs = {"test", "staging", "production"}
        if environment not in allowed_envs:
            raise ValueError("Environment must be test, staging, or production")
        if not application or not version.startswith("sha256:"):
            raise ValueError("Application and an immutable sha256 digest are required")
        with self.lock:
            existing = next((d for d in self.deployments if d["application"] == application and d["environment"] == environment), None)
            if existing:
                existing["previous"] = existing["version"]
                existing["version"] = version
                existing["status"] = "healthy"
                existing["updated"] = utc_now()
                deployment = deepcopy(existing)
            else:
                deployment = {"application": application, "environment": environment, "version": version, "previous": None, "status": "healthy", "updated": utc_now()}
                self.deployments.append(deployment)
            self.audit.append({"time": utc_now(), "actor": "release-approver", "action": "deployment.promoted", "target": f"{application}/{environment}"})
        return deployment

    def rollback(self, application: str, environment: str) -> dict:
        with self.lock:
            deployment = next((d for d in self.deployments if d["application"] == application and d["environment"] == environment), None)
            if not deployment:
                raise ValueError("Deployment not found")
            if not deployment.get("previous"):
                raise ValueError("No previous digest is available")
            deployment["version"], deployment["previous"] = deployment["previous"], deployment["version"]
            deployment["status"] = "rolled-back"
            deployment["updated"] = utc_now()
            self.audit.append({"time": utc_now(), "actor": "release-approver", "action": "deployment.rolled_back", "target": f"{application}/{environment}"})
            return deepcopy(deployment)


STATE = FactoryState()


class FactoryHandler(BaseHTTPRequestHandler):
    server_version = "AIFactorySimulator/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.log_date_time_string()} {self.client_address[0]} {fmt % args}")

    def security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:")
        self.send_header("Cache-Control", "no-store")

    def send_json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if length <= 0 or length > 16_384:
            raise ValueError("JSON body must be between 1 and 16384 bytes")
        try:
            value = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValueError("Malformed JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"status": "ok", "service": "ai-factory-simulator", "time": utc_now()})
            return
        if path == "/api/catalog":
            self.send_json({"tools": CATALOG, "profiles": PROFILES})
            return
        if path == "/api/state":
            self.send_json(STATE.snapshot())
            return
        self.serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            data = self.read_json()
            if path == "/api/pipelines/run":
                self.send_json(STATE.run_pipeline(str(data.get("project", "")).strip(), str(data.get("profile", "")).strip()), HTTPStatus.CREATED)
                return
            if path == "/api/deployments/promote":
                self.send_json(STATE.promote(str(data.get("application", "")).strip(), str(data.get("environment", "")).strip(), str(data.get("version", "")).strip()), HTTPStatus.CREATED)
                return
            if path == "/api/deployments/rollback":
                self.send_json(STATE.rollback(str(data.get("application", "")).strip(), str(data.get("environment", "")).strip()))
                return
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        candidate = (STATIC_DIR / relative).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.security_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") or content_type == "application/javascript" else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_server(host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), FactoryHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("FACTORY_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FACTORY_PORT", "8080")))
    args = parser.parse_args()
    server = build_server(args.host, args.port)
    print(f"AI Software Factory simulator listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

