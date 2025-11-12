"""Services métiers pour les ventes."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.db import transaction

from dynamic_shop.inventory.models import Product, Warehouse
from dynamic_shop.inventory.services import reserve_for_order as reserve_batch, ship_order as ship_batch

from .models import Customer, Order, OrderItem


@dataclass
class OrderItemData:
    product: Product
    quantity: int
    unit_price: Decimal


@transaction.atomic
def create_order(customer: Customer, warehouse: Warehouse, items: Iterable[OrderItemData], notes: str = "") -> Order:
    """Crée une commande à partir d'une structure simple."""

    order = Order.objects.create(customer=customer, warehouse=warehouse, notes=notes)
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
    order.refresh_total()
    return order


@transaction.atomic
def confirm_order(order: Order) -> Order:
    """Réserve les stocks nécessaires et passe la commande en confirmé."""

    if order.status != Order.Status.DRAFT:
        raise ValueError("Seules les commandes brouillon peuvent être confirmées.")
    for item in order.items.select_related("product"):
        batch = reserve_batch(item.product, item.quantity, order.warehouse)
        item.batch = batch
        item.save(update_fields=["batch"])
    order.status = Order.Status.CONFIRMED
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def ship_order(order: Order) -> Order:
    """Expédie la commande en déduisant définitivement les stocks."""

    if order.status not in {Order.Status.CONFIRMED, Order.Status.PAID}:
        raise ValueError("La commande doit être confirmée avant expédition.")
    for item in order.items.select_related("product", "batch"):
        if item.batch is None:
            raise ValueError("Chaque ligne doit avoir un lot réservé avant expédition.")
        ship_batch(item.product, item.batch, item.quantity, order.warehouse)
    order.status = Order.Status.SHIPPED
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def cancel_order(order: Order) -> Order:
    """Annule une commande et libère les réservations éventuelles."""

    if order.status == Order.Status.CANCELLED:
        return order
    if order.status == Order.Status.SHIPPED:
        raise ValueError("Impossible d'annuler une commande déjà expédiée.")
    for item in order.items.select_related("batch", "product"):
        if item.batch:
            item.batch = None
            item.save(update_fields=["batch"])
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order
