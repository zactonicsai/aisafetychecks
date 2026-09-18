"use strict";

const ui = {
  catalog: [],
  profiles: {},
  state: { deployments: [], audit: [] },
  fontSizes: [16, 18, 20],
  fontIndex: 0,
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed: ${response.status}`);
  return body;
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = String(value ?? "");
  return node.innerHTML;
}

function toast(message) {
  const node = document.querySelector("#toast");
  node.textContent = message;
  node.classList.add("show");
  window.setTimeout(() => node.classList.remove("show"), 2600);
}

function renderCatalog(filter = "") {
  const query = filter.trim().toLowerCase();
  const tools = ui.catalog.filter((tool) => `${tool.name} ${tool.category} ${tool.purpose} ${tool.tier}`.toLowerCase().includes(query));
  document.querySelector("#catalogGrid").innerHTML = tools.map((tool) => `
    <article class="card">
      <div class="meta"><span class="eyebrow">${escapeHtml(tool.category)}</span><span class="tag neutral">${escapeHtml(tool.tier)}</span></div>
      <h3>${escapeHtml(tool.name)}</h3>
      <p>${escapeHtml(tool.purpose)}</p>
    </article>`).join("") || "<p>No matching tools.</p>";
}

function renderDeployments() {
  document.querySelector("#deploymentGrid").innerHTML = ui.state.deployments.map((item) => `
    <article class="card">
      <div class="meta"><span class="eyebrow">${escapeHtml(item.environment)}</span><span class="tag ${item.status === "healthy" ? "green" : "blue"}">${escapeHtml(item.status)}</span></div>
      <h3>${escapeHtml(item.application)}</h3>
      <p>Current immutable artifact</p><code>${escapeHtml(item.version)}</code>
      <p>Previous known-good artifact</p><code>${escapeHtml(item.previous || "none")}</code>
      <div class="card-actions"><button class="danger rollback" data-app="${escapeHtml(item.application)}" data-env="${escapeHtml(item.environment)}" type="button">Simulate rollback</button></div>
    </article>`).join("");
  document.querySelectorAll(".rollback").forEach((button) => button.addEventListener("click", async () => {
    try {
      await api("/api/deployments/rollback", { method: "POST", body: JSON.stringify({ application: button.dataset.app, environment: button.dataset.env }) });
      await loadState();
      toast(`Rolled back ${button.dataset.app} in ${button.dataset.env}`);
    } catch (error) { toast(error.message); }
  }));
}

function renderAudit() {
  document.querySelector("#auditBody").innerHTML = [...ui.state.audit].reverse().map((item) => `
    <tr><td>${escapeHtml(item.time)}</td><td>${escapeHtml(item.actor)}</td><td>${escapeHtml(item.action)}</td><td>${escapeHtml(item.target)}</td></tr>`).join("");
}

async function loadState() {
  ui.state = await api("/api/state");
  renderDeployments();
  renderAudit();
}

function renderRun(run) {
  document.querySelector("#runTitle").textContent = `${run.project} · ${run.id}`;
  const status = document.querySelector("#runStatus");
  status.textContent = run.status;
  status.className = "tag green";
  document.querySelector("#stageList").innerHTML = run.stages.map((stage) => `<li><span>${escapeHtml(stage.name)}</span><span class="stage-pass">passed · ${stage.duration_seconds}s</span></li>`).join("");
  const artifact = document.querySelector("#artifactBox");
  artifact.classList.remove("hidden");
  artifact.innerHTML = `<b>Evidence envelope</b><br>Artifact: ${escapeHtml(run.artifact)}<br>SBOM: ${escapeHtml(run.sbom)} · Signed: ${run.signed ? "yes" : "no"}`;
}

function bindNavigation() {
  document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
    document.querySelectorAll(".tab, .view").forEach((node) => node.classList.remove("active"));
    tab.classList.add("active");
    document.querySelector(`#${tab.dataset.view}`).classList.add("active");
  }));
}

async function init() {
  bindNavigation();
  const catalog = await api("/api/catalog");
  ui.catalog = catalog.tools;
  ui.profiles = catalog.profiles;
  document.querySelector("#toolCount").textContent = ui.catalog.length;
  document.querySelector("#profileSelect").innerHTML = Object.keys(ui.profiles).map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
  renderCatalog();
  await loadState();

  document.querySelector("#catalogSearch").addEventListener("input", (event) => renderCatalog(event.target.value));
  document.querySelector("#pipelineForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = new FormData(event.target);
    try {
      const run = await api("/api/pipelines/run", { method: "POST", body: JSON.stringify({ project: values.get("project"), profile: values.get("profile") }) });
      renderRun(run);
      await loadState();
      toast(`Pipeline ${run.id} passed`);
    } catch (error) { toast(error.message); }
  });
  document.querySelector("#themeButton").addEventListener("click", (event) => {
    document.body.classList.toggle("dark");
    event.target.textContent = document.body.classList.contains("dark") ? "Light mode" : "Dark mode";
  });
  document.querySelector("#fontButton").addEventListener("click", () => {
    ui.fontIndex = (ui.fontIndex + 1) % ui.fontSizes.length;
    document.documentElement.style.setProperty("--base-size", `${ui.fontSizes[ui.fontIndex]}px`);
    toast(`Text size ${ui.fontSizes[ui.fontIndex]} pixels`);
  });
}

window.addEventListener("DOMContentLoaded", () => init().catch((error) => toast(error.message)));

