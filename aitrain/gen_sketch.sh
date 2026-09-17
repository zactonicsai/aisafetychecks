#!/usr/bin/env bash
# gen_sketch.sh -- ask the local iot-helper model for code, save it, compile it, optionally upload it
#   usage: ./gen_sketch.sh "Blink LED, pin 9, 500 ms, Arduino C++."  [--name blink] [--upload] [--monitor]
#   env:   MODEL_NAME (default iot-helper)  FQBN (default arduino:avr:uno)  PORT (auto-detected)
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-iot-helper}"
FQBN="${FQBN:-arduino:avr:uno}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
OUT_DIR="${OUT_DIR:-generated}"

PROMPT="${1:-}"; shift || true
[[ -z "$PROMPT" ]] && { echo "usage: $0 \"your request\" [--name NAME] [--upload] [--monitor]"; exit 2; }

NAME=""; UPLOAD=0; MONITOR=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)    NAME="$2"; shift 2 ;;
    --upload)  UPLOAD=1; shift ;;
    --monitor) MONITOR=1; shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
done
[[ -z "$NAME" ]] && NAME="sketch_$(date +%Y%m%d_%H%M%S)"

# 1) ask the model
RESPONSE=$(curl -s "$OLLAMA_URL/api/chat" -H 'Content-Type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"model": sys.argv[1], "stream": False, "messages": [{"role":"user","content": sys.argv[2]}]}))' "$MODEL_NAME" "$PROMPT")") \
  || { echo "Could not reach Ollama at $OLLAMA_URL. Is it running?"; exit 1; }

# 2) pull out the code block (prints: LANG on line 1, code after; or NONE)
PARSED=$(python3 - "$RESPONSE" <<'PY'
import json, re, sys
try:
    answer = json.loads(sys.argv[1])["message"]["content"].strip()
except Exception as e:
    print("ERROR"); print(sys.argv[1][:400]); sys.exit(0)
m = re.match(r"```(cpp|python)\n(.*?)\n```\s*$", answer, re.S)
if m:
    print(m.group(1)); print(m.group(2))
else:
    print("NONE"); print(answer)
PY
)
LANG_TAG=$(printf '%s\n' "$PARSED" | head -1)
CODE=$(printf '%s\n' "$PARSED" | tail -n +2)

case "$LANG_TAG" in
  ERROR) echo "Bad reply from Ollama:"; echo "$CODE"; exit 1 ;;
  NONE)  echo "The model did not return code. It said:"; echo; echo "$CODE"; exit 3 ;;
esac

mkdir -p "$OUT_DIR"

# 3) Python answers: save + syntax check, then stop (upload MicroPython with mpremote by hand)
if [[ "$LANG_TAG" == "python" ]]; then
  FILE="$OUT_DIR/$NAME.py"
  printf '%s\n' "$CODE" > "$FILE"
  echo "Saved MicroPython/PC Python to $FILE"
  python3 -m py_compile "$FILE" && echo "Syntax OK" || { echo "Syntax ERROR"; exit 4; }
  echo "MicroPython board:  mpremote connect \${PORT} fs cp $FILE :main.py && mpremote connect \${PORT} repl"
  exit 0
fi

# 4) C++ answers: save as an Arduino sketch and compile
SKETCH_DIR="$OUT_DIR/$NAME"
mkdir -p "$SKETCH_DIR"
FILE="$SKETCH_DIR/$NAME.ino"
printf '%s\n' "$CODE" > "$FILE"
echo "Saved Arduino sketch to $FILE"
echo "----------------------------------------"; cat "$FILE"; echo "----------------------------------------"

echo "Compiling for $FQBN ..."
if arduino-cli compile --fqbn "$FQBN" "$SKETCH_DIR" 2>&1 | tail -n 6; then
  echo "Compile OK"
else
  echo "Compile FAILED"; exit 5
fi

# 5) optional upload + serial monitor
if (( UPLOAD )); then
  if [[ -z "${PORT:-}" ]]; then
    PORT=$(arduino-cli board list --format json 2>/dev/null | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    ports=d.get("detected_ports", d if isinstance(d,list) else [])
    for p in ports:
        addr=p.get("port",{}).get("address","")
        if addr.startswith("/dev/cu.usb"): print(addr); break
except Exception: pass')
  fi
  [[ -z "${PORT:-}" ]] && { echo "No board found. Plug it in, or set PORT=/dev/cu.usbmodemXXXX"; exit 6; }
  echo "Read the sketch above. Upload to $PORT? [y/N] "; read -r yn
  [[ "$yn" =~ ^[Yy]$ ]] || { echo "Skipped upload."; exit 0; }
  arduino-cli upload -p "$PORT" --fqbn "$FQBN" "$SKETCH_DIR" && echo "Upload OK"
  if (( MONITOR )); then
    echo "Serial monitor at 9600 baud (Ctrl-C to stop)"
    arduino-cli monitor -p "$PORT" --config baudrate=9600
  fi
fi
