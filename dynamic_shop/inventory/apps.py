from __future__ import annotations

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Configuration de l'application inventaire."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dynamic_shop.inventory"
    verbose_name = "Inventaire"

    def ready(self) -> None:  # pragma: no cover - import tardif
        from . import signals  # noqa: F401
