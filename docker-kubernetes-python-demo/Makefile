# Convenience targets. Every target is a thin wrapper around a script you can read.
SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

help: ## show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-22s\033[0m %s\n",$$1,$$2}'

# ---- config -----------------------------------------------------------------
validate: ## validate app.config.yaml against schema/app-config.schema.json
	python3 tools/appconfig.py validate
show: ## print a summary of app.config.yaml
	python3 tools/appconfig.py show
render: ## render build/ (helm values, config.env, host config, cloud-init, compose)
	python3 tools/appconfig.py render all
new-project: ## NAME=my-shop DEST=../my-shop  create a new project from this template
	./scripts/new-project-from-template.sh $(NAME) $(DEST)

# ---- local: docker only ---------------------------------------------------------
compose-up: render ## run web+api with docker compose (no Kubernetes)
	docker compose -f build/docker-compose.yaml --project-directory . up --build -d
compose-down: ## stop the compose stack
	docker compose -f build/docker-compose.yaml --project-directory . down

# ---- local: kind --------------------------------------------------------------
up: ## local kind: check, cluster, build, load, deploy, test
	./scripts/run-all.sh
test: ## run the local test suite against the running app
	./scripts/05-test.sh
open: ## port-forward the public service(s)
	./scripts/06-port-forward.sh
scale-load: ## generate CPU load and watch the HPA scale
	./scripts/07-scale.sh load 60
down: ## remove the app (keep the cluster)
	./scripts/10-cleanup-apps.sh
destroy: ## delete the kind cluster
	./scripts/99-destroy.sh

# ---- azure (az cli) ------------------------------------------------------------
az-up: ## full Azure path: login, ACR, images, AKS, Key Vault, deploy, test
	./scripts/azure/run-all.sh
az-vm: ## create the base Linux VM configured by cloud-init
	./scripts/azure/10-create-vm.sh
az-ansible: ## configure the VM with Ansible
	./scripts/azure/11-run-ansible.sh
az-status: ## list Azure resources
	./scripts/azure/12-status.sh
az-destroy: ## delete the Azure resource group
	./scripts/azure/99-destroy.sh

# ---- terraform -------------------------------------------------------------------
tf-fmt: ## format + validate every terraform root
	terraform fmt -recursive terraform
	for d in terraform/local-docker terraform/local-kind terraform/azure; do (cd $$d && terraform init -backend=false -input=false >/dev/null && terraform validate); done
tf-local-docker: ## terraform apply: app on plain docker + base host container
	cd terraform/local-docker && terraform init && terraform apply
tf-local-kind: ## terraform apply: kind cluster + helm release
	cd terraform/local-kind && terraform init && terraform apply
tf-azure: ## terraform apply: ACR + AKS + Key Vault + VM
	cd terraform/azure && terraform init && terraform apply
tf-destroy-%: ## tf-destroy-local-docker | tf-destroy-local-kind | tf-destroy-azure
	cd terraform/$* && terraform destroy

# ---- quality ---------------------------------------------------------------------
lint: validate ## shellcheck, helm lint, kubeconform, ansible-lint, terraform fmt
	shellcheck -x -S warning scripts/*.sh scripts/lib/*.sh scripts/azure/*.sh setup/*.sh
	python3 tools/appconfig.py render helm >/dev/null && helm lint helm/python-demo -f build/helm-values.yaml
	helm template python-demo helm/python-demo -f build/helm-values.yaml | kubeconform -strict -summary
	kubeconform -strict -summary k8s/*.yaml
	cd ansible && ansible-lint --offline site.yml
	terraform fmt -check -recursive terraform
clean: ## remove generated files
	rm -rf build terraform/*/generated terraform/*/.terraform __pycache__ apps/*/__pycache__

.PHONY: help validate show render new-project compose-up compose-down up test open scale-load down destroy \
        az-up az-vm az-ansible az-status az-destroy tf-fmt tf-local-docker tf-local-kind tf-azure lint clean
