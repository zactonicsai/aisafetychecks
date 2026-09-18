#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
PROVIDER=${1:-}
validate_provider "$PROVIDER"
IAC=$(iac_command)
DIR="$ROOT_DIR/infra/terraform/$PROVIDER"

[ -f "$DIR/terraform.tfvars" ] || fail "Create $DIR/terraform.tfvars from terraform.tfvars.example and replace placeholders."
cd "$DIR"
info "Initializing $PROVIDER infrastructure with $IAC"
"$IAC" init
"$IAC" fmt -check
"$IAC" validate
"$IAC" plan -out=tfplan
info "Review the saved plan before applying it."

