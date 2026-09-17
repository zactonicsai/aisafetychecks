#!/usr/bin/env bash
# test_sketches.sh -- regression test: send a list of requests to the model, compile every answer, print a scoreboard
#   usage: ./test_sketches.sh              (uses tests.txt next to this script; one request per line, # = comment)
#          ./test_sketches.sh my_tests.txt
#   env:   MODEL_NAME, FQBN, OLLAMA_URL as in gen_sketch.sh
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TESTS="${1:-$HERE/tests.txt}"
export OUT_DIR="${OUT_DIR:-test_output}"
[[ -f "$TESTS" ]] || { echo "No test file: $TESTS"; exit 2; }

rm -rf "$OUT_DIR"; mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/report.txt"; : > "$REPORT"
pass=0; fail=0; n=0

while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line#"${line%%[![:space:]]*}"}"                # trim leading spaces
  [[ -z "$line" || "$line" == \#* ]] && continue
  n=$((n+1))
  expect="code"
  if [[ "$line" == ASK:* ]]; then expect="ask"; line="${line#ASK:}"; fi     # model should ask a question
  if [[ "$line" == OFF:* ]]; then expect="off"; line="${line#OFF:}"; fi     # model should refuse politely
  line="${line#"${line%%[![:space:]]*}"}"

  out=$("$HERE/gen_sketch.sh" "$line" --name "t$(printf '%02d' "$n")" 2>&1); rc=$?
  case "$expect" in
    code) if [[ $rc -eq 0 ]]; then verdict="PASS"; else verdict="FAIL (rc=$rc)"; fi ;;
    ask)  if [[ $rc -eq 3 && "$out" == *"?"* ]]; then verdict="PASS"; else verdict="FAIL (expected a question)"; fi ;;
    off)  if [[ $rc -eq 3 ]]; then verdict="PASS"; else verdict="FAIL (expected a refusal)"; fi ;;
  esac
  if [[ "$verdict" == PASS ]]; then pass=$((pass+1)); else fail=$((fail+1)); fi
  printf '%-18s | %s\n' "$verdict" "$line" | tee -a "$REPORT"
  { echo "### $n: $line"; echo "$out"; echo; } >> "$OUT_DIR/full_log.txt"
done < "$TESTS"

echo "----------------------------------------" | tee -a "$REPORT"
echo "Passed $pass / $((pass+fail))   (details: $OUT_DIR/full_log.txt)" | tee -a "$REPORT"
[[ $fail -eq 0 ]]
