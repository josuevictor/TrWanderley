#!/usr/bin/env bash
# Sobe Docker TrW, inicia cloudflared (quick tunnel) e sincroniza .env com a URL gerada.
# Rode apenas em /home/josue/trw. Outros projetos no host não são alterados.
set -euo pipefail

TRW_DIR="${TRW_DIR:-/home/josue/trw}"
LOG="${TRW_DIR}/cloudflared.log"
ORIGIN="${TRW_TUNNEL_ORIGIN:-http://127.0.0.1:18080}"
COMPOSE_FILE="-f docker-compose.prod.yml"

cd "$TRW_DIR"
case "$(pwd -P)" in
  "$TRW_DIR") ;;
  *)
    echo "Abortado: cwd deve ser $TRW_DIR" >&2
    exit 1
    ;;
esac

[[ -f .env ]] || { echo "Crie .env antes (cp .env.production.example .env)." >&2; exit 1; }

command -v cloudflared >/dev/null || {
  echo "Instale cloudflared em /usr/local/bin/cloudflared" >&2
  exit 1
}

# shellcheck disable=SC1091
set -a && source .env && set +a

docker compose $COMPOSE_FILE up -d

echo "Aguardando app em ${ORIGIN}..."
for _ in $(seq 1 30); do
  if curl -sf -o /dev/null "${ORIGIN}/" 2>/dev/null; then
    break
  fi
  sleep 2
done
if ! curl -sf -o /dev/null "${ORIGIN}/" 2>/dev/null; then
  echo "App não responde em ${ORIGIN}. Veja: docker compose $COMPOSE_FILE logs web --tail 40" >&2
  exit 1
fi

pkill -f "cloudflared tunnel --url ${ORIGIN}" 2>/dev/null || true
sleep 1
: > "$LOG"

nohup cloudflared tunnel --url "$ORIGIN" >>"$LOG" 2>&1 &
CF_PID=$!

HOST=""
for _ in $(seq 1 45); do
  if grep -qE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null; then
    HOST=$(grep -oE '[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1)
    break
  fi
  if ! kill -0 "$CF_PID" 2>/dev/null; then
    echo "cloudflared encerrou. Log:" >&2
    tail -20 "$LOG" >&2
    exit 1
  fi
  sleep 1
done

if [[ -z "$HOST" ]]; then
  echo "URL trycloudflare não encontrada em ${LOG}" >&2
  tail -30 "$LOG" >&2
  exit 1
fi

"$TRW_DIR/scripts/sync-tunnel-env.sh" "$HOST"
docker compose $COMPOSE_FILE up -d

echo ""
echo "Tunnel PID: $CF_PID (log: $LOG)"
echo "URL pública: https://${HOST}/"
echo "Login:       https://${HOST}/conta/entrar/"
echo ""
echo "Se o tunnel parar, a URL morre (erro 1033). Mantenha o processo ou rode este script de novo."
