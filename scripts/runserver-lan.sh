#!/usr/bin/env bash
# Servidor Django acessível na LAN (telefone/tablet na mesma Wi‑Fi).
# Uso: ./scripts/runserver-lan.sh
# Opcional: PORT=8001 LAN_IP=192.168.1.10 ./scripts/runserver-lan.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DETECT_SCRIPT="${ROOT}/scripts/detect-lan-ip.sh"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.development}"

PORT="${PORT:-8000}"
export RUNSERVER_PORT="$PORT"
export PORT="$PORT"

if [[ ! -x "$DETECT_SCRIPT" ]]; then
  chmod +x "$DETECT_SCRIPT" 2>/dev/null || true
fi
IP="$("$DETECT_SCRIPT")"
if [[ -z "$IP" ]]; then
  echo "Não foi possível detetar o IP LAN. Defina: LAN_IP=192.168.x.x $0" >&2
  exit 1
fi

export LAN_ORIGIN="http://${IP}:${PORT}"
echo "Aceder no telemóvel (mesma Wi‑Fi): ${LAN_ORIGIN}/"
echo "LAN_ORIGIN=${LAN_ORIGIN}"
echo "Se não abrir: isolamento de cliente no router, firewall (sudo ufw allow ${PORT}/tcp), ou IP reservado no DHCP."

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

exec "$PY" manage.py runserver "0.0.0.0:${PORT}"
