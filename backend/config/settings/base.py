"""Base Django settings for the LedgerProof backend.

The default local database points at the Docker Compose PostgreSQL service. Test
settings override this with SQLite so foundation tests do not require services.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]

APP_VERSION = os.getenv("LEDGERPROOF_APP_VERSION", "0.1.0")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "ledgerproof-local-development-only")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [
    host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host
]
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "finance_assistant",
]

MIDDLEWARE = [
    "finance_assistant.telemetry.request_id.RequestIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES: list[dict[str, Any]] = []
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def database_config_from_url(url: str) -> dict[str, Any]:
    """Build a Django DATABASES entry without pulling in an extra URL parser dependency."""
    if url.startswith("sqlite:///"):
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": url.removeprefix("sqlite:///"),
        }

    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must use postgresql:// or sqlite:///")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": int(os.getenv("DJANGO_DB_CONN_MAX_AGE", "0")),
        "OPTIONS": {
            "options": "-c statement_timeout=3000",
        },
    }


DATABASES = {
    "default": database_config_from_url(
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ledgerproof")
    )
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "finance_assistant.api.exceptions.problem_details_exception_handler",
    "UNAUTHENTICATED_USER": None,
}

LEDGERPROOF = {
    "APP_VERSION": APP_VERSION,
    "REPO_ROOT": REPO_ROOT,
    "ENABLE_EVALUATION": os.getenv("LEDGERPROOF_ENABLE_EVALUATION", "false").lower()
    in {"1", "true", "yes", "on"},
    "PROMPT_VERSION": os.getenv("LEDGERPROOF_PROMPT_VERSION", "interpretation-draft-sarvam-v1"),
    "MODEL_PROVIDER": os.getenv("LEDGERPROOF_MODEL_PROVIDER", "sarvam"),
    "SARVAM_API_KEY": os.getenv("SARVAM_API_KEY", ""),
    "SARVAM_API_SUBSCRIPTION_KEY": os.getenv("SARVAM_API_SUBSCRIPTION_KEY", ""),
    "SARVAM_BASE_URL": os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1"),
    "SARVAM_MODEL_ID": os.getenv("SARVAM_MODEL_ID", "sarvam-105b-conversations"),
    "SARVAM_TIMEOUT_SECONDS": float(os.getenv("SARVAM_TIMEOUT_SECONDS", "10.0")),
    "SARVAM_TEMPERATURE": float(os.getenv("SARVAM_TEMPERATURE", "0.1")),
    "SARVAM_MAX_TOKENS": int(os.getenv("SARVAM_MAX_TOKENS", "800")),
    "SARVAM_REASONING_EFFORT": os.getenv("SARVAM_REASONING_EFFORT", "low"),
    "SARVAM_SEED": int(os.getenv("SARVAM_SEED", "20260904")),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "%(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
}
