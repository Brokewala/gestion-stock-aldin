from __future__ import annotations

from django.apps import AppConfig


class SalesConfig(AppConfig):
    """Configuration de l'application ventes."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dynamic_shop.sales"
    verbose_name = "Ventes"

    def ready(self) -> None:  # pragma: no cover
        from . import signals  # noqa: F401
