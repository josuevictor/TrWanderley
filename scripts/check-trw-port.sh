#!/usr/bin/env bash
# Lista portas em uso no host e ajuda a escolher TRW_WEB_PORT (só consulta, não altera outros serviços).
set -euo pipefail

TRW_DIR="${TRW_DIR:-/home/josue/trw}"
DEFAULT_PORT=18080
RANGE_START=18080
RANGE_END=18119

echo "=== Portas TCP em escuta (host) ==="
if command -v ss >/dev/null; then
  ss -tlnH 2>/dev/null | awk '{print $4}' | sed -n 's/.*:\([0-9]*\)$/\1/p' | sort -n | uniq | head -40
else
  netstat -tln 2>/dev/null | tail -n +3 || true
fi

echo ""
if [[ -f "$TRW_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  set -a && source "$TRW_DIR/.env" && set +a
fi
PORT="${TRW_WEB_PORT:-$DEFAULT_PORT}"

port_in_use() {
  local p="$1"
  ss -tlnH 2>/dev/null | grep -qE "(:|\\])${p}$"
}

echo "TRW_WEB_PORT atual ( .env ou padrão ): $PORT"
if port_in_use "$PORT"; then
  echo "ATENÇÃO: porta $PORT já está em uso neste servidor."
  echo "Sugestões livres na faixa reservada ao TrW ($RANGE_START–$RANGE_END):"
  for ((p = RANGE_START; p <= RANGE_END; p++)); do
    if ! port_in_use "$p"; then
      echo "  → $p"
    fi
  done
  echo ""
  echo "Ajuste TRW_WEB_PORT no $TRW_DIR/.env e o proxy nginx/caddy para a mesma porta."
  exit 1
fi

echo "OK: porta $PORT parece livre (TRW_BIND recomendado: 127.0.0.1)."
