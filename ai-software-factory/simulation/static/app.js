const VIEWS = [
  ["floor", "Floor"],
  ["arch", "Architecture"],
  ["sso", "SSO / Access"],
  ["ws", "Workbenches"],
  ["pkg", "Packages"],
  ["git", "Source"],
  ["pipe", "Pipelines"],
  ["lab", "Test lab"],
  ["ml", "Model registry"],
  ["ship", "Deploy / rollback"],
  ["know", "Team knowledge"],
  ["audit", "Change log"],
];

const state = { token: localStorage.getItem("forgeToken"), me: null, view: "floor" };

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (state.token) headers["X-Forge-Token"] = state.token;
  const res = await fetch(path, { ...opts, headers });
  if (res.status === 401) {
    state.token = null;
    localStorage.removeItem("forgeToken");
    document.getElementById("login-gate").classList.remove("hidden");
    throw new Error("unauthorized");
  }
  return res.json();
}

function el(html) {
  const d = document.createElement("div");
  d.innerHTML = html.trim();
  return d.firstElementChild;
}

function renderNav() {
  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  VIEWS.forEach(([id, label]) => {
    const b = document.createElement("button");
    b.textContent = label;
    if (state.view === id) b.classList.add("on");
    b.onclick = () => {
      state.view = id;
      render();
    };
    nav.appendChild(b);
  });
  if (state.me) {
    document.getElementById("who").innerHTML = `${state.me.name}<br><span class="tiny">${state.me.groups.join(", ")}</span>`;
  }
}

async function viewFloor() {
  const floor = await api("/api/floor");
  const runs = await api("/api/runs");
  const cards = floor.stations
    .map(
      (s) => `<article class="card"><div class="status">● ${s.status}</div><h3>${s.name}</h3>
      <p class="tiny">${s.count != null ? s.count + " items" : "identity plane"}</p></article>`
    )
    .join("");
  return `
    <h2>Factory floor</h2>
    <p class="lede">Stations a developer walks: SSO → workbench → packages → git → custom pipeline →
    tests / model eval → signed image → GitOps to Docker/Podman/k3s/AKS/GKE/EKS. The portal never becomes a second source of truth; it drives Git.</p>
    <div class="flow">
      <span class="n">Mac / Coder workbench</span><span class="arrow">→</span>
      <span class="n">Forgejo</span><span class="arrow">→</span>
      <span class="n">Catalog pipeline</span><span class="arrow">→</span>
      <span class="n">Harbor + MLflow</span><span class="arrow">→</span>
      <span class="n">GitOps</span><span class="arrow">→</span>
      <span class="n">${floor.targets.join(" · ")}</span>
    </div>
    <div class="grid cards">${cards}</div>
    <p class="callout" style="margin-top:16px">${floor.note}</p>
    <h3 style="margin-top:28px">Recent batches</h3>
    ${renderRuns(runs.slice(0, 5))}
  `;
}

function viewArch() {
  return `
    <h2>Architecture &amp; golden path</h2>
    <p class="lede">Three portable contracts only: Git repo, OCI image (and ModelKit), Kubernetes manifest.
    Identity is Keycloak. IaC is OpenTofu. Cluster apps are GitOps. Full write-up is in <code>ARCHITECTURE.md</code>.</p>
    <div class="grid two">
      <div class="panel">
        <pre class="arch">People ── Keycloak SSO + groups
   │
Floor ── portal / catalog / audit
   │
┌──┴───┬────────┬─────────┬──────────┐
Git   Pkgs    Knowledge  Metrics
Forgejo Nexus   Outline   Prom/Graf
+DVC  Harbor   Mattermost Loki
   │
Workbench image (Java C++ Py Go Rust Node)
Colima/Podman on Mac · Coder on k3s
   │ git push
Tekton / Woodpecker catalog
build → test → eval → sbom → sign
   │
Harbor + MLflow + MinIO
   │ GitOps (Argo CD or Flux)
k3s / AKS / GKE / EKS  (+ KServe)</pre>
      </div>
      <div class="panel procon">
        <dt>Keycloak vs Authentik</dt>
        <dd>Keycloak: mature federation. Authentik: lighter. Pick one IdP.</dd>
        <dt>Forgejo vs GitLab CE</dt>
        <dd>Forgejo is small enough to operate. GitLab is a factory by itself — often too much.</dd>
        <dt>Tekton vs Woodpecker</dt>
        <dd>Tekton if CI should be K8s-native. Woodpecker if YAML and a weekend install matter more.</dd>
        <dt>Argo CD vs Flux</dt>
        <dd>Argo = UI the org will use. Flux = smaller, Git-only. Never both.</dd>
        <dt>OpenTofu vs Terraform</dt>
        <dd>Terraform is BUSL (IBM). OpenTofu stays MPL / OSI.</dd>
        <dt>Kubeflow</dt>
        <dd>Skip the umbrella. Jupyter + Tekton + MLflow + KServe covers most teams.</dd>
        <dt>Gotcha — Mac</dt>
        <dd>Produce linux images, not darwin. Bind mounts are slow; keep builds on the Linux disk.</dd>
        <dt>Gotcha — multi-cloud</dt>
        <dd>Do not write AKS/GKE/EKS YAML in app repos. Only the tofu module knows the cloud.</dd>
      </div>
    </div>
  `;
}

async function viewSso() {
  return `
    <h2>Single sign-on &amp; access</h2>
    <p class="lede">One Keycloak realm. Groups map to Forgejo, Harbor, Nexus, Coder, CI, Argo CD, Grafana, MLflow (oauth2-proxy), Outline, Mattermost, and the Kubernetes API.</p>
    <div class="grid two">
      <div class="panel">
        <p class="tiny">Current session</p>
        <p><strong>${state.me.name}</strong> · <code>${state.me.username}</code></p>
        <p>Groups: ${state.me.groups.map((g) => `<span class="pill ok">${g}</span>`).join(" ")}</p>
        <p class="tiny">Issuer: keycloak://forge/realms/internal</p>
      </div>
      <div class="panel">
        <table>
          <tr><th>Group</th><th>Can do</th></tr>
          <tr><td>platform</td><td>Break-glass cluster, catalogs, tofu</td></tr>
          <tr><td>ml-engineer</td><td>Push models, run eval, promote to stage</td></tr>
          <tr><td>developer</td><td>Write team repos, run CI, ns-dev</td></tr>
          <tr><td>reviewer</td><td>Approve GitOps PRs to prod</td></tr>
        </table>
      </div>
    </div>
    <p class="callout" style="margin-top:16px">Pods do not use user SSO tokens. Workload identity (IRSA / Entra Workload ID / GKE WIF) is a separate plane. Mixing them is a common outage.</p>
  `;
}

async function viewWs() {
  const list = await api("/api/workspaces");
  const rows = list
    .map(
      (w) => `<tr><td>${w.name}</td><td>${w.owner}</td><td><code>${w.runtime}</code></td>
      <td>${w.toolchains.join(", ")}</td><td><span class="pill ok">${w.status}</span></td></tr>`
    )
    .join("");
  return `
    <h2>Linux workbenches</h2>
    <p class="lede">The developer VM is a disposable Linux container/VM from <code>platform/workbench</code>.
    Compilers and test tools are already on PATH. Extra packages come from Nexus, not the public internet.
    On a Mac: Colima or Podman Machine. Remote: Coder on k3s.</p>
    <div class="row" style="margin-bottom:12px">
      <input id="ws-name" placeholder="workspace name" style="max-width:240px" />
      <select id="ws-rt" style="max-width:200px">
        <option value="colima-podman">colima-podman (Mac)</option>
        <option value="coder-k3s">coder-k3s (remote)</option>
        <option value="lima-ubuntu">lima-ubuntu VM</option>
      </select>
      <button class="good" id="ws-start">Start workbench</button>
    </div>
    <div class="panel"><table>
      <tr><th>Name</th><th>Owner</th><th>Runtime</th><th>Toolchains</th><th>Status</th></tr>
      ${rows}
    </table></div>
    <p class="tiny" style="margin-top:10px">Preinstalled: JDK 21, gcc/clang, CMake, Python+uv, Go, Rust, Node, pytest, JUnit, GoogleTest, Playwright, k6, syft, grype, cosign, MLflow CLI, DVC, kit.</p>
  `;
}

async function viewPkg() {
  const items = await api("/api/packages");
  const rows = items
    .map(
      (p) => `<tr><td><span class="pill">${p.ecosystem}</span></td><td>${p.name}</td><td>${p.version}</td><td>${p.channel}</td></tr>`
    )
    .join("");
  return `
    <h2>Package &amp; image repositories</h2>
    <p class="lede">Nexus proxies PyPI, Maven, npm, crates, Go, and apt. Harbor holds OCI images, Helm, and KitOps ModelKits. MinIO is the DVC/MLflow blob store. Workbench <code>pip.conf</code> already points here.</p>
    <div class="row" style="margin-bottom:12px">
      <input id="pkg-q" placeholder="search pytest, junit, harbor…" style="max-width:280px" />
      <button id="pkg-go">Search</button>
    </div>
    <div class="panel"><table>
      <tr><th>Ecosystem</th><th>Package</th><th>Version</th><th>Channel</th></tr>
      ${rows}
    </table></div>
  `;
}

async function viewGit() {
  const repos = await api("/api/repos");
  const rows = repos
    .map(
      (r) => `<tr><td><code>${r.name}</code></td><td>${r.desc}</td><td>${r.default_branch}</td><td>${r.commits}</td></tr>`
    )
    .join("");
  return `
    <h2>Source control (Forgejo)</h2>
    <p class="lede">Check in code here. Large datasets and weights go through DVC pointers, not Git blobs. GitOps desired state lives in <code>gitops/clusters</code>.</p>
    <div class="row" style="margin-bottom:12px">
      <input id="repo-name" placeholder="team/new-harness" style="max-width:260px" />
      <button class="good" id="repo-new">Create repo</button>
    </div>
    <div class="panel"><table>
      <tr><th>Repo</th><th>Description</th><th>Branch</th><th>Commits</th></tr>
      ${rows}
    </table></div>
  `;
}

function renderRuns(runs) {
  if (!runs.length) return `<p class="muted">No pipeline batches yet.</p>`;
  return runs
    .map((r) => {
      const stages = r.stages
        .map((s) => `<span class="st ${s.status}">${s.id} · ${s.status}</span>`)
        .join("");
      return `<div class="panel" style="margin-bottom:10px">
        <div class="row" style="justify-content:space-between">
          <strong>${r.project}</strong>
          <span class="pill ${r.status === "passed" ? "ok" : "stg"}">${r.status}</span>
        </div>
        <p class="tiny">${r.template} → ${r.target} · actor ${r.actor} · ${r.id}${r.digest ? " · " + r.digest : ""}</p>
        <div class="stages">${stages}</div>
      </div>`;
    })
    .join("");
}

async function viewPipe() {
  const templates = await api("/api/templates");
  const runs = await api("/api/runs");
  const opts = templates.map((t) => `<option value="${t.id}">${t.id} (${t.languages.join(", ")})</option>`).join("");
  return `
    <h2>Pipeline factory</h2>
    <p class="lede">Developers do not invent a CI system. They pick a catalog template and add tasks — including a unique testing tool published by another team. Same stages locally and in the cloud.</p>
    <div class="panel" style="margin-bottom:16px">
      <div class="grid three">
        <label class="tiny">Project<input id="p-proj" value="models/fraud-ranker" /></label>
        <label class="tiny">Template<select id="p-tpl">${opts}</select></label>
        <label class="tiny">Target
          <select id="p-tgt">
            <option>k3s</option><option>docker</option><option>podman</option>
            <option>aks</option><option>gke</option><option>eks</option>
          </select>
        </label>
      </div>
      <div class="row" style="margin-top:12px">
        <button class="primary" id="p-run" style="width:auto">Build · test · stage · ship</button>
      </div>
    </div>
    ${renderRuns(runs)}
  `;
}

function viewLab() {
  return `
    <h2>Test lab — languages and web</h2>
    <p class="lede">Every workbench image and every catalog template uses the same harness names so a custom tool can plug in.</p>
    <div class="grid two">
      <div class="panel">
        <h3>Language tests</h3>
        <table>
          <tr><th>Language</th><th>Build</th><th>Test</th><th>Static</th></tr>
          <tr><td>Python</td><td>uv / pip</td><td>pytest</td><td>ruff, mypy</td></tr>
          <tr><td>Java</td><td>Maven / Gradle</td><td>JUnit 5</td><td>SpotBugs, ErrorProne</td></tr>
          <tr><td>C/C++</td><td>CMake + Ninja</td><td>GoogleTest</td><td>clang-tidy, sanitizers</td></tr>
          <tr><td>Go</td><td>go build</td><td>go test</td><td>golangci-lint</td></tr>
          <tr><td>Rust</td><td>cargo</td><td>cargo test / nextest</td><td>clippy, rustfmt</td></tr>
        </table>
      </div>
      <div class="panel">
        <h3>Web &amp; system tests</h3>
        <table>
          <tr><th>Kind</th><th>Tool</th></tr>
          <tr><td>Unit UI</td><td>Vitest / Jest</td></tr>
          <tr><td>E2E</td><td>Playwright</td></tr>
          <tr><td>API contract</td><td>Schemathesis / Pact OSS</td></tr>
          <tr><td>Load</td><td>k6</td></tr>
          <tr><td>Containers</td><td>Testcontainers</td></tr>
          <tr><td>Model eval</td><td>pytest metrics vs MLflow baseline</td></tr>
        </table>
        <p class="tiny">A team can publish <code>tools/web-contract-harness</code> as a catalog task. Other pipelines add that one stage — no fork of CI.</p>
      </div>
    </div>
  `;
}

async function viewMl() {
  const models = await api("/api/models");
  const rows = models
    .map(
      (m) => `<tr><td>${m.name}</td><td>${m.version}</td>
      <td><span class="pill ${m.stage === "Production" ? "ok" : "stg"}">${m.stage}</span></td>
      <td>f1 ${m.metrics.f1} · auc ${m.metrics.auc} · p99 ${m.metrics.latency_p99_ms}ms</td>
      <td><code>${m.digest}</code></td></tr>`
    )
    .join("");
  return `
    <h2>Model registry (MLflow + ModelKit)</h2>
    <p class="lede">Experiments stream to MLflow. Immutable weights live in MinIO via DVC and/or a KitOps ModelKit on Harbor. Promotion is a stage change plus a GitOps digest bump — never a mutated file.</p>
    <div class="panel"><table>
      <tr><th>Model</th><th>Ver</th><th>Stage</th><th>Metrics</th><th>Digest</th></tr>
      ${rows}
    </table></div>
  `;
}

async function viewShip() {
  const deps = await api("/api/deployments");
  const rows = deps
    .map(
      (d) => `<tr><td>${d.app}</td><td>${d.target}</td><td>${d.env}</td>
      <td><code>${d.digest}</code></td><td>${d.git_sha}</td>
      <td><span class="pill ${d.status.includes("roll") ? "stg" : "ok"}">${d.status}</span></td></tr>`
    )
    .join("");
  return `
    <h2>Shipping dock — deploy &amp; rollback</h2>
    <p class="lede">The same image digest moves from Docker/Podman to k3s to AKS/GKE/EKS. Rollback restores the previous Git SHA in the GitOps repo. Images are never overwritten.</p>
    <div class="row" style="margin-bottom:12px">
      <select id="d-tgt"><option>k3s</option><option>docker</option><option>podman</option><option>aks</option><option>gke</option><option>eks</option></select>
      <select id="d-env"><option>stage</option><option>prod</option></select>
      <button class="good" id="d-go">GitOps sync</button>
      <button class="warn" id="d-rb">Rollback prod on AKS</button>
    </div>
    <div class="panel"><table>
      <tr><th>App</th><th>Target</th><th>Env</th><th>Digest</th><th>Git</th><th>Status</th></tr>
      ${rows}
    </table></div>
  `;
}

async function viewKnow() {
  const items = await api("/api/knowledge");
  const cards = items
    .map((k) => `<article class="card"><div class="tiny">${k.team}</div><h3>${k.title}</h3><p>${k.body}</p></article>`)
    .join("");
  return `
    <h2>Team knowledge</h2>
    <p class="lede">Outline (docs) + Mattermost (chat) + ADRs in Git. The floor can publish a note so it is not trapped in a private DM.</p>
    <div class="panel" style="margin-bottom:14px">
      <input id="k-title" placeholder="Title" />
      <textarea id="k-body" rows="3" placeholder="What should the next team know?" style="margin-top:8px"></textarea>
      <button class="good" id="k-add" style="margin-top:8px">Publish note</button>
    </div>
    <div class="grid cards">${cards}</div>
  `;
}

async function viewAudit() {
  const items = await api("/api/audit");
  const rows = items
    .map((a) => `<tr><td>${a.ts}</td><td>${a.actor}</td><td>${a.action}</td><td>${a.detail}</td></tr>`)
    .join("");
  return `
    <h2>Change log &amp; audit</h2>
    <p class="lede">SSO logins, repo creates, pipeline starts, GitOps syncs, and rollbacks. In production this is Keycloak + Forgejo + Harbor + Kubernetes audit shipped to Loki.</p>
    <div class="panel"><table>
      <tr><th>Time</th><th>Actor</th><th>Action</th><th>Detail</th></tr>
      ${rows || "<tr><td colspan=4 class='muted'>Empty — use the floor.</td></tr>"}
    </table></div>
  `;
}

const V = {
  floor: viewFloor,
  arch: viewArch,
  sso: viewSso,
  ws: viewWs,
  pkg: viewPkg,
  git: viewGit,
  pipe: viewPipe,
  lab: viewLab,
  ml: viewMl,
  ship: viewShip,
  know: viewKnow,
  audit: viewAudit,
};

async function render() {
  renderNav();
  const root = document.getElementById("app");
  root.innerHTML = "<p class='muted'>Loading…</p>";
  try {
    root.innerHTML = await V[state.view]();
  } catch (e) {
    root.innerHTML = `<p>Could not load view. Is the Python server running?</p>`;
    return;
  }
  bind();
}

function bind() {
  const $ = (id) => document.getElementById(id);
  if ($("ws-start"))
    $("ws-start").onclick = async () => {
      await api("/api/workspaces", {
        method: "POST",
        body: JSON.stringify({ name: $("ws-name").value, runtime: $("ws-rt").value }),
      });
      render();
    };
  if ($("pkg-go"))
    $("pkg-go").onclick = async () => {
      const q = $("pkg-q").value;
      const items = await api("/api/packages?q=" + encodeURIComponent(q));
      document.querySelector("#app table").tBodies[0]
        ? null
        : null;
      const html = items
        .map((p) => `<tr><td><span class="pill">${p.ecosystem}</span></td><td>${p.name}</td><td>${p.version}</td><td>${p.channel}</td></tr>`)
        .join("");
      document.querySelector("#app table").innerHTML =
        `<tr><th>Ecosystem</th><th>Package</th><th>Version</th><th>Channel</th></tr>` + html;
    };
  if ($("repo-new"))
    $("repo-new").onclick = async () => {
      await api("/api/repos", { method: "POST", body: JSON.stringify({ name: $("repo-name").value }) });
      render();
    };
  if ($("p-run"))
    $("p-run").onclick = async () => {
      await api("/api/pipelines/run", {
        method: "POST",
        body: JSON.stringify({
          project: $("p-proj").value,
          template: $("p-tpl").value,
          target: $("p-tgt").value,
          kind: $("p-tpl").value.includes("python") ? "model" : "app",
        }),
      });
      render();
      setTimeout(render, 2800);
    };
  if ($("d-go"))
    $("d-go").onclick = async () => {
      await api("/api/deploy", {
        method: "POST",
        body: JSON.stringify({ target: $("d-tgt").value, env: $("d-env").value, app: "fraud-ranker" }),
      });
      render();
    };
  if ($("d-rb"))
    $("d-rb").onclick = async () => {
      await api("/api/rollback", { method: "POST", body: JSON.stringify({ target: "aks", env: "prod" }) });
      render();
    };
  if ($("k-add"))
    $("k-add").onclick = async () => {
      await api("/api/knowledge", {
        method: "POST",
        body: JSON.stringify({ title: $("k-title").value, body: $("k-body").value }),
      });
      render();
    };
}

async function afterLogin(data) {
  state.token = data.token;
  state.me = data;
  localStorage.setItem("forgeToken", data.token);
  document.getElementById("login-gate").classList.add("hidden");
  await render();
}

document.getElementById("login-btn").onclick = async () => {
  const data = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("user").value,
      password: document.getElementById("pass").value,
    }),
  }).then((r) => r.json());
  if (data.error) {
    alert(data.error);
    return;
  }
  afterLogin(data);
};

(async () => {
  if (!state.token) return;
  try {
    const me = await api("/api/me");
    state.me = me;
    document.getElementById("login-gate").classList.add("hidden");
    await render();
  } catch {
    /* stay on gate */
  }
})();
