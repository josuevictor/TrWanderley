#!/usr/bin/env bash
# Deploy isolado: altera SOMENTE o diretório TRW (padrão /home/josue/trw).
set -euo pipefail

TRW_DIR="${TRW_DIR:-/home/josue/trw}"
REPO_URL="${REPO_URL:-https://github.com/josuevictor/TrWanderley.git}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="-f docker-compose.prod.yml"

cd "$TRW_DIR"
case "$(pwd -P)" in
  "$TRW_DIR") ;;
  *)
    echo "Abortado: cwd não é $TRW_DIR" >&2
    exit 1
    ;;
esac

if [[ ! -f .env ]]; then
  echo "Crie .env a partir de .env.production.example antes de subir." >&2
  exit 1
fi

# shellcheck disable=SC1091
set -a && source .env && set +a
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-trw}"

TRW_BIND="${TRW_BIND:-127.0.0.1}"
TRW_WEB_PORT="${TRW_WEB_PORT:-18080}"

if [[ "$TRW_BIND" != "127.0.0.1" && "$TRW_BIND" != "localhost" ]]; then
  echo "Aviso: TRW_BIND=$TRW_BIND expõe o app na rede; use 127.0.0.1 atrás do nginx." >&2
fi

if [[ -x "$TRW_DIR/scripts/check-trw-port.sh" ]]; then
  TRW_DIR="$TRW_DIR" "$TRW_DIR/scripts/check-trw-port.sh"
fi

if [[ ! -d .git ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" .
else
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

docker compose $COMPOSE_FILE up -d --build

echo ""
echo "Projeto Docker: $COMPOSE_PROJECT_NAME (containers trw-*)"
echo "App em http://${TRW_BIND}:${TRW_WEB_PORT}/"
echo "Próximo: proxy reverso (nginx/caddy) → http://127.0.0.1:${TRW_WEB_PORT}"
