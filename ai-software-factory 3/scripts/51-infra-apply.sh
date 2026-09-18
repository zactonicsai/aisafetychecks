#!/usr/bin/env sh
set -eu
. "$(dirname "$0")/lib/common.sh"
PROVIDER=${1:-}
validate_provider "$PROVIDER"
IAC=$(iac_command)
DIR="$ROOT_DIR/infra/terraform/$PROVIDER"
[ -f "$DIR/tfplan" ] || fail "No saved plan. Run ./scripts/50-infra-plan.sh $PROVIDER first."

cd "$DIR"
info "Applying the reviewed saved plan for $PROVIDER"
"$IAC" apply tfplan
info "Infrastructure created. Run ./scripts/60-cloud-deploy.sh $PROVIDER"

