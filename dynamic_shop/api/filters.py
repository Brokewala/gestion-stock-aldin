"""Filtres DRF pour les endpoints."""
from __future__ import annotations

import django_filters
from django.utils import timezone

from dynamic_shop.inventory.models import Batch, Product
from dynamic_shop.sales.models import Order


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="iexact")
    brand = django_filters.CharFilter(field_name="brand__name", lookup_expr="iexact")
    min_stock = django_filters.NumberFilter(field_name="remaining_stock", lookup_expr="gte")
    max_stock = django_filters.NumberFilter(field_name="remaining_stock", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["category", "brand", "is_active"]


class BatchFilter(django_filters.FilterSet):
    near_expiry = django_filters.BooleanFilter(method="filter_near_expiry")

    class Meta:
        model = Batch
        fields = ["product__sku", "warehouse__name"]

    def filter_near_expiry(self, queryset, name, value):
        if value:
            limit = timezone.now().date() + timezone.timedelta(days=30)
            return queryset.filter(expiry_date__isnull=False, expiry_date__lte=limit)
        return queryset


class OrderFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["status", "customer__name"]
