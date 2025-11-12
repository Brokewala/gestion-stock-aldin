"""Signaux dédiés à la synchronisation des stocks."""
from __future__ import annotations

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Batch, Product, update_product_stock

LOGGER = logging.getLogger(__name__)


@receiver(post_save, sender=Batch)
def update_stock_on_save(sender, instance: Batch, **_: object) -> None:
    """Recalcule le stock agrégé à chaque sauvegarde de lot."""

    update_product_stock(instance.product)
    if instance.product.is_below_reorder:
        LOGGER.warning("Produit %s sous le seuil de réapprovisionnement", instance.product.sku)


@receiver(post_delete, sender=Batch)
def update_stock_on_delete(sender, instance: Batch, **_: object) -> None:
    """Recalcule le stock à la suppression d'un lot."""

    update_product_stock(instance.product)


@receiver(post_save, sender=Product)
def alert_on_reorder(sender, instance: Product, **_: object) -> None:
    """Journalise un avertissement lorsque le seuil est dépassé."""

    if instance.is_below_reorder:
        LOGGER.warning("Alerte réapprovisionnement pour %s", instance.sku)
