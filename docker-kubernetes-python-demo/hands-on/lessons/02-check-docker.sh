#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/common.sh"

title "Lesson 02: verify the Docker engine"
explain "docker info asks the Docker daemon for its status. kind needs this engine because every Kubernetes node will be a Docker container."
need docker
run docker info
explain "docker ps now lists running containers. Before cluster creation, no docker-k8 nodes may appear."
run docker ps
