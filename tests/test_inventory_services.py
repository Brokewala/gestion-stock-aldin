from __future__ import annotations

from datetime import date

import pytest
from dynamic_shop.inventory.models import Batch, Product, Warehouse
from dynamic_shop.inventory.services import (
    PurchaseItem,
    adjust_stock,
    receive_purchase,
    reserve_for_order,
    transfer_stock,
)


@pytest.mark.django_db
def test_receive_purchase_creates_batches(product: Product, warehouse: Warehouse):
    items = [PurchaseItem(product=product, quantity=100, batch_code="B1", expiry_date=date.today())]
    receive_purchase("Test", items, warehouse)
    batch = Batch.objects.get(batch_code="B1")
    assert batch.initial_qty == 100
    assert batch.remaining_qty == 100
    product.refresh_from_db()
    assert product.remaining_stock == 100


@pytest.mark.django_db
def test_transfer_stock_moves_between_warehouses(product: Product, warehouse: Warehouse):
    other = Warehouse.objects.create(name="Second")
    receive_purchase("Test", [PurchaseItem(product=product, quantity=50, batch_code="B2")], warehouse)
    batch = Batch.objects.get(batch_code="B2")
    transfer_stock(product, 20, warehouse, other, batch=batch)
    dest = Batch.objects.get(batch_code="B2", warehouse=other)
    assert dest.remaining_qty == 20
    batch.refresh_from_db()
    assert batch.remaining_qty == 30


@pytest.mark.django_db
def test_adjust_stock_positive(product: Product, warehouse: Warehouse):
    batch = Batch.objects.create(
        product=product,
        batch_code="B3",
        initial_qty=0,
        remaining_qty=0,
        warehouse=warehouse,
    )
    adjust_stock(product, warehouse, 15, reason="Inventaire", batch=batch)
    batch.refresh_from_db()
    assert batch.remaining_qty == 15


@pytest.mark.django_db
def test_reserve_for_order_checks_quantity(product: Product, warehouse: Warehouse):
    receive_purchase("Test", [PurchaseItem(product=product, quantity=10, batch_code="B4")], warehouse)
    batch = reserve_for_order(product, 5, warehouse)
    assert batch.batch_code == "B4"
    with pytest.raises(ValueError):
        reserve_for_order(product, 20, warehouse)


@pytest.mark.django_db
def test_adjust_stock_negative_error(product: Product, warehouse: Warehouse):
    batch = Batch.objects.create(
        product=product,
        batch_code="B5",
        initial_qty=10,
        remaining_qty=10,
        warehouse=warehouse,
    )
    adjust_stock(product, warehouse, -5, reason="Casse", batch=batch)
    batch.refresh_from_db()
    assert batch.remaining_qty == 5
