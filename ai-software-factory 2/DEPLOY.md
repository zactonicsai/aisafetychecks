# Deploy Aether Forge (static + localStorage)

The factory floor is a static site. All simulation state (repos, pipelines, models, SSO session) lives in the **browser `localStorage`**. No Python, no database, no Vercel serverless functions required.

## Vercel (recommended)

From the repo root:

```bash
npm i -g vercel
vercel
```

Accept the defaults. `vercel.json` rewrites `/` to `simulation/static/`.

Or in the Vercel dashboard:

1. Import the Git repo
2. Framework Preset: **Other**
3. Root Directory: leave blank (uses repo-root `vercel.json`)  
   **or** set Root Directory to `simulation/static`
4. Deploy

## Local static (no Python)

```bash
cd simulation/static
python3 -m http.server 8080
```

Open http://127.0.0.1:8080

You can also open `index.html` directly; most browsers allow localStorage on `file://`.

## Optional Python API

`simulation/app.py` is still there if you want a shared process-side API. The HTML no longer depends on it.

## Data

| Key | What |
|---|---|
| `aether-forge-state-v1` | packages, repos, workspaces, runs, models, deploys, knowledge, audit |
| `aether-forge-session-v1` | current SSO user |

Reset from **SSO / Access → Reset factory data**, or clear site data in the browser.

This is per-browser and per-origin. Two teammates on Vercel do not share state unless you later add a real backend.
