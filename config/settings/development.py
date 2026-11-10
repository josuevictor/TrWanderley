"""Development settings — DEBUG on, local-friendly defaults."""

import os
import socket

from .base import *  # noqa: F403

DEBUG = True

# Qualquer Host (localhost e IP da LAN) — para testar no telemóvel com runserver 0.0.0.0:8000
# sem exportar DJANGO_ALLOW_LAN. Só usar este settings module em desenvolvimento.
ALLOWED_HOSTS = ["*"]


def _detect_lan_ip() -> str | None:
    """IP da interface usada para sair à rede (costuma ser o Wi‑Fi/Ethernet ativo)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        # Não envia tráfego; só escolhe a rota local
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        return None
    if not ip or ip.startswith("127."):
        return None
    return ip


def _dev_server_port() -> str:
    return (
        os.environ.get("RUNSERVER_PORT")
        or os.environ.get("PORT")
        or os.environ.get("DJANGO_DEV_PORT")
        or "8000"
    ).strip()


# CSRF no telemóvel: o Referer tem de ser uma origem confiável (http://IP:porta).
# LAN_ORIGIN / CSRF_TRUSTED_ORIGINS no .env continuam a funcionar.
# Se o IP mudar (DHCP), com DEV_AUTO_LAN_CSRF=1 (default) acrescentamos
# http://<IP-detectado>:<porta> automaticamente (porta = RUNSERVER_PORT ou 8000).
def _merge_csrf_origins() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    port = _dev_server_port()
    for o in (
        f"http://127.0.0.1:{port}",
        f"http://localhost:{port}",
    ):
        if o not in seen:
            seen.add(o)
            out.append(o)
    extra = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
    if extra:
        for x in extra.split(","):
            x = x.strip()
            if x and x not in seen:
                seen.add(x)
                out.append(x)
    lan = os.environ.get("LAN_ORIGIN", "").strip()
    if lan and lan not in seen:
        seen.add(lan)
        out.append(lan)

    auto = os.environ.get("DEV_AUTO_LAN_CSRF", "1").lower() in ("1", "true", "yes")
    if auto:
        ip = _detect_lan_ip()
        if ip:
            origin = f"http://{ip}:{port}"
            if origin not in seen:
                seen.add(origin)
                out.append(origin)

    return out


CSRF_TRUSTED_ORIGINS = _merge_csrf_origins()

# SQLite fallback if you run without PostgreSQL locally (override in .env)
if os.environ.get("USE_SQLITE", "").lower() in ("1", "true", "yes"):  # noqa: F405
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }
