"""Production settings — load from environment."""

import os

from .base import *  # noqa: F403

DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

allowed = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in allowed.split(",") if h.strip()]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
