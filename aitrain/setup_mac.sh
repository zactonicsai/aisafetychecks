#!/usr/bin/env bash
# setup_mac.sh -- one-time setup on macOS for the Arduino IoT code helper
#   installs: Homebrew (if missing), arduino-cli, Ollama, Python venv + pyserial + mpremote,
#             the Arduino AVR core (Uno/Nano/Mega), DHT + Servo libraries
#   usage:    ./setup_mac.sh            (add  --esp32  to also install the ESP32 Arduino core)
set -euo pipefail

WANT_ESP32=0
[[ "${1:-}" == "--esp32" ]] && WANT_ESP32=1

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '   \033[1;32m✔ %s\033[0m\n' "$*"; }
warn() { printf '   \033[1;33m! %s\033[0m\n' "$*"; }

# 1) Homebrew
if ! command -v brew >/dev/null 2>&1; then
  log "Installing Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Apple Silicon puts brew in /opt/homebrew; make it visible in this shell
  [[ -x /opt/homebrew/bin/brew ]] && eval "$(/opt/homebrew/bin/brew shellenv)"
fi
ok "Homebrew $(brew --version | head -1)"

# 2) arduino-cli, ollama, python
log "Installing arduino-cli, ollama, python (skips anything already present)"
brew list arduino-cli >/dev/null 2>&1 || brew install arduino-cli
brew list ollama      >/dev/null 2>&1 || brew install ollama
brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
ok "arduino-cli $(arduino-cli version | awk '{print $3}')"
ok "ollama $(ollama --version 2>/dev/null | awk '{print $NF}')"

# 3) Python virtual environment for the helper scripts
log "Python virtual environment (venv/)"
if [[ ! -d venv ]]; then python3 -m venv venv; fi
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install --quiet pyserial mpremote
ok "pyserial + mpremote installed in venv/"

# 4) Arduino cores and libraries
log "Arduino cores and libraries"
arduino-cli config init --overwrite >/dev/null 2>&1 || true
if (( WANT_ESP32 )); then
  arduino-cli config add board_manager.additional_urls \
    https://espressif.github.io/arduino-esp32/package_esp32_index.json >/dev/null 2>&1 || true
fi
arduino-cli core update-index
arduino-cli core install arduino:avr
if (( WANT_ESP32 )); then arduino-cli core install esp32:esp32; fi
arduino-cli lib install "DHT sensor library" "Adafruit Unified Sensor" Servo
ok "cores: $(arduino-cli core list | tail -n +2 | awk '{print $1}' | tr '\n' ' ')"

# 5) Ollama service + model check
log "Ollama"
if ! curl -s http://localhost:11434/api/tags >/dev/null; then
  warn "Ollama is not running. Start it with:  brew services start ollama   (or open the Ollama app)"
else
  if curl -s http://localhost:11434/api/tags | grep -q '"iot-helper'; then
    ok "model iot-helper is loaded"
  else
    warn "model iot-helper not found. From the folder with your Modelfile run:  ollama create iot-helper -f Modelfile"
  fi
fi

# 6) Board check
log "Connected boards"
arduino-cli board list || true

cat <<'MSG'

Done. Next:
  source venv/bin/activate
  ./gen_sketch.sh "Blink LED, pin 9, 500 ms, Arduino C++."      # generate + compile
  ./test_sketches.sh                                             # run the built-in test set
  ./gen_sketch.sh "..." --upload                                 # generate, compile, upload
MSG
