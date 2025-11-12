"""Signaux pour automatiser la gestion des commandes."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, OrderItem, Payment


def generate_order_code() -> str:
    """Génère un code unique de type ORD-YYYYMMDD-XXXX."""

    today = timezone.now().strftime("%Y%m%d")
    last_order = Order.objects.filter(code__startswith=f"ORD-{today}").order_by("code").last()
    if last_order:
        last_increment = int(last_order.code.split("-")[-1])
    else:
        last_increment = 0
    return f"ORD-{today}-{last_increment + 1:04d}"


@receiver(pre_save, sender=Order)
def assign_order_code(sender, instance: Order, **_: Any) -> None:
    """Assigne un code à la création."""

    if not instance.code:
        instance.code = generate_order_code()


@receiver(pre_save, sender=OrderItem)
def compute_line_total(sender, instance: OrderItem, **_: Any) -> None:
    """Calcule le total ligne avant sauvegarde."""

    instance.compute_total()


def _update_order_total(order: Order) -> None:
    order.compute_totals()
    order.save(update_fields=["total_amount", "updated_at"])


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def refresh_order_total(sender, instance: OrderItem, **_: Any) -> None:
    """Met à jour le total de commande à chaque modification de ligne."""

    _update_order_total(instance.order)


@receiver(post_save, sender=Payment)
def update_status_on_payment(sender, instance: Payment, **_: Any) -> None:
    """Passe la commande en état payé si le cumul atteint le total."""

    order = instance.order
    total_paid = order.payments.aggregate(total=models.Sum("amount")).get("total") or Decimal("0")
    if total_paid >= order.total_amount and order.status in {Order.Status.CONFIRMED, Order.Status.PAID}:
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated_at"])
