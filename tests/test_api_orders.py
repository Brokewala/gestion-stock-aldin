from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from dynamic_shop.inventory.services import PurchaseItem, receive_purchase
from dynamic_shop.sales.models import Customer
from dynamic_shop.sales.services import OrderItemData, create_order


@pytest.mark.django_db
def test_order_actions(api_client, product, warehouse):
    customer = Customer.objects.create(name="API Client")
    receive_purchase("Test", [PurchaseItem(product=product, quantity=60, batch_code="API1")], warehouse)
    order = create_order(
        customer=customer,
        warehouse=warehouse,
        items=[OrderItemData(product=product, quantity=10, unit_price=Decimal("1500"))],
    )
    url = reverse("order-confirm", args=[order.pk])
    response = api_client.post(url)
    assert response.status_code == 200
    url = reverse("order-cancel", args=[order.pk])
    response = api_client.post(url)
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    # shipping after cancellation should échouer
    url = reverse("order-ship", args=[order.pk])
    response = api_client.post(url)
    assert response.status_code == 400
