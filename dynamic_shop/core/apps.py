from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration de l'application principale (pages publiques)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dynamic_shop.core"
    verbose_name = "Noyau"
