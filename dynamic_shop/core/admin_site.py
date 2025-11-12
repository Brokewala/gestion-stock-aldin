"""Customisation du site d'administration avec tableau de bord enrichi."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import List

from django.contrib import admin
from django.db.models import F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from dynamic_shop.inventory.models import Batch, Product
from dynamic_shop.sales.models import Order, OrderItem


@dataclass
class SalesSerie:
    labels: List[str]
    data: List[float]


def _build_sales_series(now) -> SalesSerie:
    """Construit la série de ventes sur 30 jours pour Chart.js."""

    since = now - timedelta(days=30)
    daily = (
        OrderItem.objects.filter(order__created_at__gte=since)
        .annotate(day=TruncDate("order__created_at"))
        .values("day")
        .annotate(total=Sum("line_total"))
        .order_by("day")
    )

    labels = [entry["day"].strftime("%d/%m") if entry["day"] else "" for entry in daily]
    data = [float(entry["total"] or Decimal("0")) for entry in daily]
    return SalesSerie(labels=labels, data=data)


class DynamicAdminSite(admin.site.__class__):
    """Étend le site admin actuel pour injecter les KPI et graphiques."""

    site_header = "DYNAMIC Backoffice"
    site_title = "DYNAMIC Admin"
    index_title = "Tableau de bord"
    index_template = "admin/index.html"

    def each_context(self, request):  # type: ignore[override]
        context = super().each_context(request)
        now = timezone.now()
        since = now - timedelta(days=30)

        orders_count = Order.objects.filter(created_at__gte=since).count()
        revenue = (
            OrderItem.objects.filter(order__created_at__gte=since)
            .aggregate(total=Sum("line_total"))
            .get("total")
            or Decimal("0")
        )
        low_stock = (
            Product.objects.filter(is_active=True)
            .filter(remaining_stock__lte=F("reorder_level"))
            .count()
        )
        expiring_batches = (
            Batch.objects.filter(expiry_date__isnull=False)
            .filter(expiry_date__lte=now.date() + timedelta(days=30))
            .count()
        )

        sales_series = _build_sales_series(now)

        context["kpi"] = {
            "orders_30d": orders_count,
            "revenue_30d": f"{revenue:,.0f}".replace(",", " "),
            "low_stock": low_stock,
            "expiring_30d": expiring_batches,
        }
        context["charts"] = {
            "sales": {
                "labels": sales_series.labels,
                "data": sales_series.data,
            }
        }
        return context


# Patch de l'instance admin globale pour conserver les enregistrements existants.
admin.site.__class__ = DynamicAdminSite
admin.site.site_header = DynamicAdminSite.site_header
admin.site.site_title = DynamicAdminSite.site_title
admin.site.index_title = DynamicAdminSite.index_title
