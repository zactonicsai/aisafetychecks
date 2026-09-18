#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
PROVIDER=${1:-}
validate_provider "$PROVIDER"

case "$PROVIDER" in
  aws)
    need aws
    aws sts get-caller-identity
    ;;
  azure)
    need az
    az account show --output table
    ;;
  gcp)
    need gcloud
    gcloud auth list
    gcloud config list project
    ;;
esac

