"""Paramétrage principal du projet DYNAMIC Shop."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import dj_database_url
from dotenv import load_dotenv

# Chargement des variables d'environnement dès le démarrage.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Gestion des secrets et des paramètres sensibles.
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-en-production")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = ["gestion-stock-aldin.onrender.com","127.0.0.1", "localhost"]

# Applications installées.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "jazzmin",
    "whitenoise.runserver_nostatic",
    # Apps tierces
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    "django_filters",
    "import_export",
    "channels",
    # Apps projet
    "dynamic_shop.core",
    "dynamic_shop.inventory",
    "dynamic_shop.sales",
    "dynamic_shop.chatbot",
    "dynamic_shop.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dynamic_shop.dynamic_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dynamic_shop.core.context_processors.dashboard_metrics",
            ],
        },
    },
]

WSGI_APPLICATION = "dynamic_shop.dynamic_shop.wsgi.application"
ASGI_APPLICATION = "dynamic_shop.dynamic_shop.asgi.application"

# Configuration Channels : mémoire pour le dev, Redis optionnel.
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

# Base de données avec fallback SQLite.
DATABASES: Dict[str, Any] = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Configuration internationale.
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Nairobi")
USE_I18N = True
USE_TZ = True

# Fichiers statiques et médias.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"



MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuration DRF générale.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/day",
        "anon": "200/day",
    },
}

# Jazzmin : personnalisation de l'interface d'administration.
JAZZMIN_SETTINGS = {
    "site_title": "DYNAMIC Admin",
    "site_header": "DYNAMIC Backoffice",
    "welcome_sign": "Bienvenue sur DYNAMIC",
    "site_brand": "DYNAMIC",
    "site_logo": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?auto=format&fit=crop&w=200&q=80",
    "login_logo": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?auto=format&fit=crop&w=200&q=80",
    "topmenu_links": [
        {"name": "Accueil", "url": "core:home", "permissions": ["auth.view_user"]},
        {"name": "Documentation API", "url": "api-docs"},
        {"app": "inventory"},
        {"app": "sales"},
    ],
    "icons": {
        "inventory.Product": "fas fa-bolt",
        "inventory.Supplier": "fas fa-truck",
        "inventory.Warehouse": "fas fa-warehouse",
        "sales.Order": "fas fa-shopping-cart",
        "sales.Customer": "fas fa-user",
        "sales.Payment": "fas fa-credit-card",
    },
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_models": ["auth.Group"],
    "order_with_respect_to": ["inventory", "sales"],
    "custom_links": {
        "inventory": [
            {
                "name": "Rapport de stock bas",
                "url": "core:low-stock-report",
                "icon": "fas fa-exclamation-triangle",
            }
        ],
        "sales": [
            {
                "name": "Commandes du jour",
                "url": "core:dashboard",
                "icon": "fas fa-chart-line",
            }
        ],
    },
    "related_modal_active": True,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "cyborg",
    "dark_mode_theme": "darkly",
    "navbar_small_text": False,
    "brand_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "sidebar_fixed": True,
    "navbar": "navbar-indigo navbar-dark",
}

# Configuration Swagger/Redoc.
SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": True,
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        }
    },
}

# WhiteNoise : compression automatique.
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30

# Emplacement du fichier env pour la documentation.
ENV_FILE_PATH = BASE_DIR / ".env"
WHITENOISE_MANIFEST_STRICT = False
