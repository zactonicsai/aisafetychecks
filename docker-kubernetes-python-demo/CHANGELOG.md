# Changelog

## 2.0.0 — template + Azure + Terraform + Ansible expansion

### Added
- `app.config.yaml` + `schema/app-config.schema.json`: one schema-validated file describing services,
  ports (`expose: none|cluster|public`), config settings, secret keys, image/file sources, scaling,
  network rules, base-Linux host setup and deployment targets.
- `tools/appconfig.py`: validate / show / render (Helm values, `config.env`, host config,
  per-service env files, cloud-init, docker-compose, secrets values).
- `scripts/azure/`: complete `az` CLI path — login, RG + ACR, `az acr build`, AKS (Cilium network
  policy, autoscaler, ACR attach, workload identity, Key Vault CSI addon), credentials, Helm deploy
  with LoadBalancer, tests, pod/node scaling, Key Vault secrets, NSG/LB lockdown, base Linux VM via
  cloud-init, Ansible run, status, destroy.
- `terraform/`: shared `modules/app-config`; roots `local-docker` (plain Docker + base host
  container), `local-kind` (kind + metrics-server + Helm), `azure` (ACR, AKS, Key Vault, VM with
  NSG rules from the schema, Helm release, Ansible inventory).
- `setup/setup.sh` + `setup/configure.sh`: idempotent base-Linux host configuration (packages,
  Docker, ufw, users, timezone, downloaded files with sha256 checks, settings, containers with
  password-less ACR pull via managed identity).
- `ansible/`: playbook + `base-linux` role that reads `app.config.yaml` directly.
- Local scripts 07 (scaling), 08 (secrets), 09 (network), 10 (cleanup), template bootstrap script,
  metrics-server install for HPA demos, network-policy negative test.
- `docs/`: middle-school-level tutorial with grocery-store/school analogies, phase-by-phase
  walkthroughs, Azure, Terraform, schema, host-setup, best-practices/pros-cons, cheat sheet,
  troubleshooting.
- `Makefile`, `.env.example`, `secrets.env.example`, CI workflow, `TEMPLATE.md`.

### Changed
- Helm chart rewritten as a generic loop over `services`; adds ConfigMap, Secret, HPA,
  NetworkPolicy (default-deny + allow-lists), Ingress, ServiceAccount, `helm test`,
  checksum annotations, `loadBalancerSourceRanges`, stricter pod security.
- Kubernetes resource names are now `<app>-<service>` (`python-demo-web`) instead of `python-web`.
- The chart no longer creates the Namespace (use `--create-namespace`, the standard practice).
- Apps: web calls the api over the cluster network, both expose `/config`, api exposes
  `/api/work` (CPU burn for HPA demos); images are multi-stage, non-root, run gunicorn.
- Raw `k8s/` manifests extended with namespace, ConfigMaps, example Secret, HPA, NetworkPolicies.
- Scripts are schema-driven (no hard-coded names) and Helm-4 aware.

## 1.0.0
- Original kind + Helm + two Flask apps demo.
