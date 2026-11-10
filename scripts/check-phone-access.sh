#!/usr/bin/env bash
# Diagnóstico rápido: URL para o telemóvel + teste local à porta
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DETECT="${ROOT}/scripts/detect-lan-ip.sh"
chmod +x "$DETECT" 2>/dev/null || true
PORT="${PORT:-8000}"

echo "=== IP sugerido para o telemóvel ==="
IP="$("$DETECT" || true)"
if [[ -z "$IP" ]]; then
  echo "Falhou deteção. Corra: LAN_IP=10.0.0.x $DETECT"
  exit 1
fi
echo "http://${IP}:${PORT}/"
echo ""
echo "=== Porta ${PORT} a escutar (deve ter 0.0.0.0) ==="
ss -tlnp 2>/dev/null | grep ":${PORT} " || echo "(ss não mostrou — corra o runserver com 0.0.0.0:${PORT})"
echo ""
echo "=== Teste HTTP no próprio PC (via IP LAN) ==="
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://${IP}:${PORT}/" | grep -qE '200|301|302'; then
  echo "OK — servidor responde em http://${IP}:${PORT}/"
else
  echo "Falhou curl para http://${IP}:${PORT}/ — o runserver está a correr?"
fi
