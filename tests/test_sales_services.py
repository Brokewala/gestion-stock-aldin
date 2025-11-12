from __future__ import annotations

from decimal import Decimal

import pytest

from dynamic_shop.inventory.models import Batch, Product, Warehouse
from dynamic_shop.inventory.services import PurchaseItem, receive_purchase
from dynamic_shop.sales.models import Customer
from dynamic_shop.sales.services import OrderItemData, cancel_order, confirm_order, create_order, ship_order


@pytest.mark.django_db
def test_order_confirmation_and_shipping(product: Product, warehouse: Warehouse):
    customer = Customer.objects.create(name="Client Test")
    receive_purchase("Test", [PurchaseItem(product=product, quantity=80, batch_code="CONF1")], warehouse)
    order = create_order(
        customer=customer,
        warehouse=warehouse,
        items=[OrderItemData(product=product, quantity=20, unit_price=Decimal("1500"))],
    )
    confirm_order(order)
    order.refresh_from_db()
    assert order.status == order.Status.CONFIRMED
    line = order.items.first()
    assert line and line.batch is not None
    ship_order(order)
    order.refresh_from_db()
    assert order.status == order.Status.SHIPPED


@pytest.mark.django_db
def test_cancel_order_releases_batch(product: Product, warehouse: Warehouse):
    customer = Customer.objects.create(name="Client Test")
    receive_purchase("Test", [PurchaseItem(product=product, quantity=40, batch_code="CONF2")], warehouse)
    order = create_order(
        customer=customer,
        warehouse=warehouse,
        items=[OrderItemData(product=product, quantity=10, unit_price=Decimal("1500"))],
    )
    confirm_order(order)
    cancel_order(order)
    order.refresh_from_db()
    assert order.status == order.Status.CANCELLED
    assert order.items.first().batch is None
