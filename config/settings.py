"""Configuración del Taller #3 de Lotería Binaria.

La fase inicial usa SQLite. MySQL se habilita únicamente en la segunda
fase del taller. PostgreSQL está bloqueado expresamente para esta entrega.
"""

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    DJANGO_DEMO_PASSWORD=(str, ""),
)
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

_development_key = "django-insecure-development-only-change-me"
SECRET_KEY = env("DJANGO_SECRET_KEY", default=_development_key)
if not DEBUG and SECRET_KEY == _development_key:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY debe configurarse cuando DJANGO_DEBUG=False."
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts.apps.AccountsConfig",
    "apps.core.apps.CoreConfig",
    "apps.finance.apps.FinanceConfig",
    "apps.vendors.apps.VendorsConfig",
    "apps.lottery.apps.LotteryConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

_database = env.db_url("DATABASE_URL", default="sqlite:///db.sqlite3")
_allowed_engines = {
    "django.db.backends.sqlite3",
    "django.db.backends.mysql",
}
if _database.get("ENGINE") not in _allowed_engines:
    raise ImproperlyConfigured(
        "Este Taller #3 admite únicamente SQLite en fase 1 y MySQL en fase 2."
    )
if _database.get("ENGINE") == "django.db.backends.sqlite3":
    sqlite_name = _database.get("NAME")
    if sqlite_name and sqlite_name != ":memory:":
        sqlite_path = Path(sqlite_name)
        if not sqlite_path.is_absolute():
            _database["NAME"] = BASE_DIR / sqlite_path
elif _database.get("ENGINE") == "django.db.backends.mysql":
    _database.setdefault("OPTIONS", {})
    _database["OPTIONS"].setdefault("charset", "utf8mb4")
    _database["OPTIONS"].setdefault(
        "init_command",
        "SET sql_mode='STRICT_TRANS_TABLES'",
    )
DATABASES = {"default": _database}

# Normaliza rutas relativas de SQLite bajo la raíz del proyecto.
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    sqlite_database_name = str(DATABASES["default"]["NAME"])

    if sqlite_database_name != ":memory:":
        sqlite_database_path = Path(sqlite_database_name)

        if not sqlite_database_path.is_absolute():
            DATABASES["default"]["NAME"] = (
                BASE_DIR / sqlite_database_path
            ).resolve()

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        )
    },
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

DEMO_PASSWORD = env("DJANGO_DEMO_PASSWORD")
