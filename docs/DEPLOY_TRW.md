# Deploy no servidor (somente `/home/josue/trw`)

Não alterar outros projetos em `/home/josue`. Tudo abaixo roda **apenas** dentro de `trw`.

## Pré-requisitos no servidor

- Docker e `docker compose` (plugin v2)
- Acesso git ao repositório (HTTPS ou deploy key)
- Porta livre em localhost (padrão **18080** — configurável via `TRW_WEB_PORT`)

## 1. Primeira vez (diretório vazio)

```bash
cd /home/josue/trw
git clone https://github.com/josuevictor/TrWanderley.git .
cp .env.production.example .env
nano .env   # SECRET_KEY, senhas, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, TRW_WEB_PORT
chmod +x scripts/deploy-trw-server.sh
./scripts/deploy-trw-server.sh
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Gerar `SECRET_KEY` (no laptop ou no servidor):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 2. Atualizações

```bash
cd /home/josue/trw
./scripts/deploy-trw-server.sh
```

## 3. Proxy HTTPS (no host, fora do Docker)

Exemplo nginx (site novo, não mexer nos vhosts dos outros apps):

```nginx
server {
    listen 443 ssl;
    server_name trw.seudominio.com.br;
  # ssl_certificate ... (certbot ou certificado existente)

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Ajuste `18080` se mudou `TRW_WEB_PORT` no `.env`.

## 4. O que o `docker-compose.prod.yml` faz

- Postgres **sem** porta publicada no host
- `collectstatic` antes do Gunicorn
- Web só em `127.0.0.1:TRW_WEB_PORT` (evita conflito com outros serviços na 8000)

## 5. Backup rápido

```bash
cd /home/josue/trw
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup-$(date +%F).sql
```
