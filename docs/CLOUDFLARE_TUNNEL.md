# Cloudflare quick tunnel (PWA / celular)

Só afeta **TrW** em `/home/josue/trw` → `http://127.0.0.1:18080`.

## Um comando (recomendado)

```bash
cd /home/josue/trw
git pull
chmod +x scripts/start-cloudflared-trw.sh scripts/sync-tunnel-env.sh
./scripts/start-cloudflared-trw.sh
```

O script:

1. Sobe `docker compose -f docker-compose.prod.yml`
2. Inicia `cloudflared` em background
3. Lê a URL `*.trycloudflare.com` do log
4. Corrige **ALLOWED_HOSTS** e **CSRF_TRUSTED_ORIGINS** no `.env` (mesmo host, sem barra extra)
5. Reinicia o container web

Use a URL impressa (`/conta/entrar/`). **Não reutilize** URLs antigas — quick tunnel gera host novo a cada execução.

## Erros

| Código | Causa |
|--------|--------|
| **1033** | `cloudflared` parado ou URL antiga no navegador |
| **502** | App não responde em `127.0.0.1:18080` |
| **400 DisallowedHost** | Rode `./scripts/sync-tunnel-env.sh SEU-HOST.trycloudflare.com` e `docker compose -f docker-compose.prod.yml up -d` |

## Atualizar host manualmente

```bash
./scripts/sync-tunnel-env.sh widgets-abc-def.trycloudflare.com
docker compose -f docker-compose.prod.yml up -d
```

## Ver tunnel

```bash
tail -f /home/josue/trw/cloudflared.log
ps aux | grep '[c]loudflared tunnel'
```
