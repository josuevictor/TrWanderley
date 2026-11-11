#!/usr/bin/env bash
# Atualiza ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS no .env para o host do trycloudflare / domínio.
# Uso: ./scripts/sync-tunnel-env.sh nome.trycloudflare.com
#      ./scripts/sync-tunnel-env.sh 'https://nome.trycloudflare.com/'
set -euo pipefail

TRW_DIR="${TRW_DIR:-/home/josue/trw}"
RAW="${1:-}"

if [[ -z "$RAW" ]]; then
  echo "Uso: $0 <hostname ou URL https>" >&2
  exit 1
fi

HOST="$RAW"
HOST="${HOST#https://}"
HOST="${HOST#http://}"
HOST="${HOST%%/*}"
HOST="${HOST%%\#*}"

if [[ "$HOST" != *.* ]]; then
  echo "Host inválido: $HOST" >&2
  exit 1
fi

cd "$TRW_DIR"
[[ -f .env ]] || { echo "Arquivo .env não encontrado em $TRW_DIR" >&2; exit 1; }

ALLOWED="${HOST},localhost,127.0.0.1"
CSRF="https://${HOST}"

if grep -q '^ALLOWED_HOSTS=' .env; then
  sed -i "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${ALLOWED}|" .env
else
  echo "ALLOWED_HOSTS=${ALLOWED}" >> .env
fi

if grep -q '^CSRF_TRUSTED_ORIGINS=' .env; then
  sed -i "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${CSRF}|" .env
else
  echo "CSRF_TRUSTED_ORIGINS=${CSRF}" >> .env
fi

echo "OK .env:"
grep -E '^ALLOWED_HOSTS=|^CSRF_TRUSTED_ORIGINS=' .env
