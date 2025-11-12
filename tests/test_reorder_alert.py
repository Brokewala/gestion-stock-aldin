from __future__ import annotations

import pytest

from dynamic_shop.inventory.models import Product


@pytest.mark.django_db
def test_is_below_reorder(product: Product):
    product.remaining_stock = 5
    product.reorder_level = 10
    product.save()
    assert product.is_below_reorder is True
