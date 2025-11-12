"""Vues publiques et tableau de bord pour DYNAMIC."""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from dynamic_shop.inventory.models import Batch, Product
from dynamic_shop.sales.models import Order


def home(request: HttpRequest) -> HttpResponse:
    """Affiche la landing page marketing."""

    featured_products: List[Product] = Product.objects.filter(is_active=True)[:3]
    stats = {
        "total_stock": Batch.objects.aggregate(total=Sum("remaining_qty"))["total"] or 0,
        "orders_today": Order.objects.filter(created_at__date=timezone.now().date()).count(),
        "low_stock": Product.objects.filter(remaining_stock__lte=F("reorder_level"), is_active=True).count(),
    }
    context: Dict[str, object] = {
        "featured_products": featured_products,
        "stats": stats,
    }
    return render(request, "core/home.html", context)


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard analytique destiné aux équipes internes."""

    today = timezone.now().date()
    month_start = today.replace(day=1)
    kpis = {
        "total_stock": Batch.objects.aggregate(total=Sum("remaining_qty"))["total"] or 0,
        "orders_month": Order.objects.filter(created_at__date__gte=month_start).count(),
        "potential_shortages": Product.objects.filter(remaining_stock__lte=F("reorder_level"), is_active=True),
        "near_expiry": Batch.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=timezone.now() + timedelta(days=30),
        ),
    }

    orders_qs = (
        Order.objects.filter(created_at__date__gte=month_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("items__line_total"))
        .order_by("day")
    )
    orders_series = [
        {
            "day": entry["day"].strftime("%Y-%m-%d") if entry["day"] else None,
            "total": float(entry["total"] or 0),
        }
        for entry in orders_qs
    ]
    stock_series = [
        {"warehouse__name": entry["warehouse__name"], "total": int(entry["total"] or 0)}
        for entry in Batch.objects.values("warehouse__name").annotate(total=Sum("remaining_qty")).order_by("warehouse__name")
    ]

    context = {
        "kpis": kpis,
        "orders_series": orders_series,
        "stock_series": stock_series,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def low_stock_report(request: HttpRequest) -> HttpResponse:
    """Rapport listant les produits en dessous du seuil de réapprovisionnement."""

    products = Product.objects.filter(is_active=True, remaining_stock__lte=F("reorder_level")).select_related(
        "brand", "category"
    )
    return render(request, "core/low_stock_report.html", {"products": products})
