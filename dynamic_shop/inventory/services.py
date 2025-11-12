"""Services métier pour la gestion des stocks DYNAMIC."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    Batch,
    Product,
    StockMovement,
    Warehouse,
    ensure_non_negative,
    pick_batch,
    update_product_stock,
)


@dataclass
class PurchaseItem:
    """Structure décrivant un article réceptionné."""

    product: Product
    quantity: int
    batch_code: Optional[str] = None
    expiry_date: Optional[date] = None


def generate_batch_code(product: Product) -> str:
    """Génère un code lot simple basé sur la date et le SKU."""

    suffix = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"{product.sku}-{suffix}"


@transaction.atomic
def receive_purchase(
    supplier_name: str,
    items: Iterable[PurchaseItem],
    warehouse: Warehouse,
    created_by=None,
) -> List[Batch]:
    """Enregistre une réception fournisseur et crée les lots associés."""

    created_batches: List[Batch] = []
    for item in items:
        batch = Batch.objects.create(
            product=item.product,
            batch_code=item.batch_code or generate_batch_code(item.product),
            expiry_date=item.expiry_date,
            initial_qty=0,
            remaining_qty=0,
            warehouse=warehouse,
        )
        StockMovement.objects.create(
            product=item.product,
            batch=batch,
            movement_type=StockMovement.MovementType.IN,
            quantity=item.quantity,
            to_warehouse=warehouse,
            reason=f"Réception {supplier_name}",
            created_by=created_by,
        )
        created_batches.append(batch)
    return created_batches


@transaction.atomic
def transfer_stock(
    product: Product,
    quantity: int,
    from_warehouse: Warehouse,
    to_warehouse: Warehouse,
    batch: Optional[Batch] = None,
    created_by=None,
) -> None:
    """Transfère une quantité d'un entrepôt à un autre."""

    if batch is None:
        batch = pick_batch(product, quantity, warehouse=from_warehouse)
        if batch is None:
            raise ValueError("Aucun lot disponible pour ce transfert.")
    ensure_non_negative(batch.remaining_qty - quantity)

    StockMovement.objects.create(
        product=product,
        batch=batch,
        movement_type=StockMovement.MovementType.TRANSFER,
        quantity=quantity,
        from_warehouse=from_warehouse,
        to_warehouse=to_warehouse,
        reason="Transfert entre entrepôts",
        created_by=created_by,
    )


@transaction.atomic
def adjust_stock(
    product: Product,
    warehouse: Warehouse,
    quantity: int,
    reason: str,
    batch: Optional[Batch] = None,
    created_by=None,
) -> Batch:
    """Ajuste un stock (inventaire physique)."""

    if batch is None:
        batch = pick_batch(product, 1, warehouse=warehouse)
        if batch is None:
            batch = Batch.objects.create(
                product=product,
                batch_code=generate_batch_code(product),
                expiry_date=None,
                initial_qty=0,
                remaining_qty=0,
                warehouse=warehouse,
            )
    movement_kwargs = {
        "product": product,
        "batch": batch,
        "movement_type": StockMovement.MovementType.ADJUSTMENT,
        "quantity": abs(quantity),
        "reason": reason,
        "created_by": created_by,
    }
    if quantity >= 0:
        movement_kwargs["to_warehouse"] = warehouse
    else:
        movement_kwargs["from_warehouse"] = warehouse
    StockMovement.objects.create(**movement_kwargs)
    return batch


@transaction.atomic
def reserve_for_order(product: Product, quantity: int, warehouse: Warehouse) -> Batch:
    """Réserve un lot complet pour une commande (FIFO)."""

    batch = pick_batch(product, quantity, warehouse=warehouse)
    if batch is None or batch.remaining_qty < quantity:
        raise ValueError("Stock insuffisant pour cette commande.")
    return batch


@transaction.atomic
def ship_order(product: Product, batch: Batch, quantity: int, warehouse: Warehouse) -> None:
    """Confirme la sortie de stock lors de l'expédition d'une commande."""

    StockMovement.objects.create(
        product=product,
        batch=batch,
        movement_type=StockMovement.MovementType.OUT,
        quantity=quantity,
        from_warehouse=warehouse,
        reason="Expédition commande",
    )


def product_stock_by_warehouse(product: Product) -> List[dict[str, int]]:
    """Retourne la ventilation du stock par entrepôt."""

    return list(
        product.batches.values("warehouse__name").annotate(total=Sum("remaining_qty")).order_by("warehouse__name")
    )


def apply_movement(movement: StockMovement) -> None:
    """Applique concrètement un mouvement de stock."""

    batch = movement.batch
    product = movement.product
    if batch is None:
        raise ValueError("Les mouvements doivent référencer un lot.")

    if movement.movement_type == StockMovement.MovementType.IN:
        batch.initial_qty += movement.quantity
        batch.remaining_qty += movement.quantity
        if movement.to_warehouse:
            batch.warehouse = movement.to_warehouse
        batch.save(update_fields=["initial_qty", "remaining_qty", "warehouse"])
    elif movement.movement_type == StockMovement.MovementType.OUT:
        ensure_non_negative(batch.remaining_qty - movement.quantity)
        batch.remaining_qty -= movement.quantity
        batch.save(update_fields=["remaining_qty"])
    elif movement.movement_type == StockMovement.MovementType.TRANSFER:
        ensure_non_negative(batch.remaining_qty - movement.quantity)
        batch.remaining_qty -= movement.quantity
        batch.save(update_fields=["remaining_qty"])
        destination, _ = Batch.objects.get_or_create(
            product=product,
            batch_code=batch.batch_code,
            warehouse=movement.to_warehouse,
            defaults={
                "expiry_date": batch.expiry_date,
                "initial_qty": 0,
                "remaining_qty": 0,
                "received_at": batch.received_at,
            },
        )
        destination.initial_qty += movement.quantity
        destination.remaining_qty += movement.quantity
        destination.save(update_fields=["initial_qty", "remaining_qty"])
    elif movement.movement_type == StockMovement.MovementType.ADJUSTMENT:
        if movement.to_warehouse:
            batch.initial_qty += movement.quantity
            batch.remaining_qty += movement.quantity
        elif movement.from_warehouse:
            ensure_non_negative(batch.remaining_qty - movement.quantity)
            batch.remaining_qty -= movement.quantity
        batch.save(update_fields=["initial_qty", "remaining_qty"])
    else:  # pragma: no cover - choix exhaustif
        raise ValueError("Type de mouvement inconnu")

    update_product_stock(product)
