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

if [[ ! -d .git ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" .
else
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

docker compose $COMPOSE_FILE up -d --build

echo ""
echo "App em http://127.0.0.1:${TRW_WEB_PORT:-18080} (veja TRW_WEB_PORT no .env)."
echo "Próximo: proxy reverso (nginx/caddy) para o domínio público → essa porta."
