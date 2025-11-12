from __future__ import annotations

import pytest
from django.contrib.auth.models import User

from dynamic_shop.inventory.models import Brand, Category, Product, Supplier, Warehouse


@pytest.fixture
@pytest.mark.django_db
def warehouse() -> Warehouse:
    return Warehouse.objects.create(name="Test WH")


@pytest.fixture
@pytest.mark.django_db
def product(warehouse: Warehouse) -> Product:
    brand, _ = Brand.objects.get_or_create(name="DYNAMIC")
    category, _ = Category.objects.get_or_create(name="Boissons")
    return Product.objects.create(
        sku="SKU-TEST",
        name="Produit Test",
        brand=brand,
        category=category,
        unit="canette",
        size_ml=250,
        flavor="Original",
        reorder_level=10,
        reorder_qty=50,
    )


@pytest.fixture
@pytest.mark.django_db
def supplier() -> Supplier:
    return Supplier.objects.create(name="Supplier Test")


@pytest.fixture
@pytest.mark.django_db
def api_client(db):  # type: ignore[override]
    from rest_framework.test import APIClient

    client = APIClient()
    user = User.objects.create_user(username="api", password="api")
    client.force_authenticate(user=user)
    return client
