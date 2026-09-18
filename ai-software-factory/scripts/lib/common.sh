#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

info() { printf '\n[INFO] %s\n' "$*"; }
warn() { printf '\n[WARN] %s\n' "$*" >&2; }
fail() { printf '\n[ERROR] %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"; }

iac_command() {
  if command -v tofu >/dev/null 2>&1; then
    printf '%s' tofu
  elif command -v terraform >/dev/null 2>&1; then
    printf '%s' terraform
  else
    fail "Install OpenTofu (preferred) or Terraform."
  fi
}

validate_provider() {
  case "$1" in
    aws|azure|gcp) ;;
    *) fail "Provider must be one of: aws, azure, gcp" ;;
  esac
}
