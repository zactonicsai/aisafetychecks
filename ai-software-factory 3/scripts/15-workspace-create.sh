#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
need limactl
need ansible-playbook

if limactl list --format '{{.Name}}' | grep -qx ai-factory; then
  info "Lima VM ai-factory already exists"
else
  info "Creating the Lima Linux VM"
  limactl create --name ai-factory "$ROOT_DIR/developer-workspace/lima.yaml"
fi
limactl start ai-factory

info "Configuring the workspace through Ansible over Lima shell"
limactl shell ai-factory sudo mkdir -p /opt/ai-factory
limactl shell ai-factory sudo chown "$(id -u):$(id -g)" /opt/ai-factory || true
tar -C "$ROOT_DIR/infra/ansible" -cf - . | limactl shell ai-factory tar -C /tmp -xf -
limactl shell ai-factory ansible-playbook -i localhost, -c local /tmp/playbooks/developer-workspace.yml --ask-become-pass

info "Workspace ready. Enter it with: limactl shell ai-factory"

