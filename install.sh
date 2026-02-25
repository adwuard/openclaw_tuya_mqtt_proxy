#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

usage() {
  cat <<'EOF'
Usage: bash install.sh [all|deps|broker|openclaw|install-mosquitto|mosquitto-listen-all|test-help]

Commands:
  all                   Run dependency + broker + openclaw checks (default)
  deps                  Install/check Python dependencies
  broker                Check/start mosquitto service if installed
  openclaw              Check openclaw command
  install-mosquitto     Install/start mosquitto (requires sudo)
  mosquitto-listen-all  Write mosquitto config to listen on 0.0.0.0:1883
  test-help             Print test commands
EOF
}

maybe_apply_mosquitto_listen_all() {
  if ! command -v mosquitto >/dev/null 2>&1; then
    return
  fi
  read -r -p "Apply Mosquitto listen-all config now (0.0.0.0:1883)? (y/N) " ans
  case "$ans" in
    [Yy]*)
      if [[ "${EUID}" -eq 0 ]]; then
        setup_mosquitto_listen_all
      else
        sudo bash "${SCRIPT_DIR}/install.sh" mosquitto-listen-all
      fi
      ;;
    *)
      echo "Skipped Mosquitto listen-all config."
      ;;
  esac
}

install_python_deps() {
  echo "[deps] Installing Python dependencies..."
  pip3 install --user -r requirements.txt 2>/dev/null \
    || pip3 install --break-system-packages -r requirements.txt 2>/dev/null \
    || (sudo apt-get update && sudo apt-get install -y python3-paho-mqtt)

  if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "paho-mqtt is still missing."
    echo "Install manually with: pip3 install --user paho-mqtt"
    exit 1
  fi
}

check_mosquitto() {
  echo "[broker] Checking MQTT broker..."
  if ! command -v mosquitto >/dev/null 2>&1; then
    echo "Mosquitto not found. Install with:"
    echo "sudo apt-get install mosquitto mosquitto-clients"
    return
  fi

  if systemctl is-active --quiet mosquitto 2>/dev/null; then
    echo "Mosquitto is running."
    return
  fi

  read -r -p "Mosquitto is installed but not running. Start it now? (y/N) " ans
  case "$ans" in
    [Yy]*)
      sudo systemctl start mosquitto
      sudo systemctl enable mosquitto
      echo "Mosquitto started and enabled."
      ;;
    *)
      echo "Skipped starting Mosquitto."
      ;;
  esac
}

check_openclaw() {
  echo "[openclaw] Checking OpenClaw..."
  if ! command -v openclaw >/dev/null 2>&1; then
    echo "OpenClaw is not installed or not in PATH."
    exit 1
  fi
  openclaw --version | sed -n '1p'
}

install_mosquitto() {
  echo "[install-mosquitto] Installing Mosquitto..."
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This command needs root privileges."
    echo "Run: sudo bash install.sh install-mosquitto"
    exit 1
  fi

  apt-get update
  apt-get install -y mosquitto mosquitto-clients
  systemctl enable --now mosquitto
  echo "Mosquitto installed and started."
}

setup_mosquitto_listen_all() {
  local template_file="${SCRIPT_DIR}/configs/mosquitto_listen_all.conf"
  local conf_file="/etc/mosquitto/conf.d/listen_all.conf"
  echo "[mosquitto-listen-all] Configuring ${conf_file} from template..."

  if [[ "${EUID}" -ne 0 ]]; then
    echo "This command needs root privileges."
    echo "Run: sudo bash install.sh mosquitto-listen-all"
    exit 1
  fi

  if [[ ! -f "${template_file}" ]]; then
    echo "Template not found: ${template_file}"
    exit 1
  fi

  cp "${template_file}" "${conf_file}"

  systemctl restart mosquitto
  if ! systemctl is-active --quiet mosquitto; then
    echo "Mosquitto failed to start. Check:"
    echo "journalctl -u mosquitto -n 100 --no-pager"
    exit 1
  fi

  echo "Mosquitto is active. Port check:"
  if command -v ss >/dev/null 2>&1; then
    ss -tlnp | rg "1883" || true
  elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | rg "1883" || true
  else
    echo "Neither ss nor netstat found; skip port check."
  fi
}

print_test_help() {
  cat <<'EOF'

Test flow:
1) python3 openclaw_mqtt_bridge.py
2) mosquitto_sub -h localhost -t openclaw/server/response -v
3) mosquitto_pub -h localhost -t openclaw/device/user_speech_text -m 'your message'

Expected:
- Bridge receives message from openclaw/device/user_speech_text
- Bridge publishes response to openclaw/server/response
EOF
}

run_all() {
  echo "MQTT-OpenClaw bridge setup"
  install_python_deps
  check_mosquitto
  maybe_apply_mosquitto_listen_all
  check_openclaw
  print_test_help
}

cmd="${1:-all}"
case "${cmd}" in
  all) run_all ;;
  deps) install_python_deps ;;
  broker) check_mosquitto ;;
  openclaw) check_openclaw ;;
  install-mosquitto) install_mosquitto ;;
  mosquitto-listen-all) setup_mosquitto_listen_all ;;
  test-help) print_test_help ;;
  -h|--help|help) usage ;;
  *)
    echo "Unknown command: ${cmd}"
    usage
    exit 1
    ;;
esac


