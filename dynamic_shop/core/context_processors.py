"""Context processors offrant des métriques globales pour les templates."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from django.db.models import F, Sum
from django.utils import timezone

from dynamic_shop.inventory.models import Batch, Product
from dynamic_shop.sales.models import Order


def dashboard_metrics(request: Any) -> Dict[str, Any]:
    """Fournit des indicateurs synthétiques affichés dans la barre de navigation."""

    total_stock = (
        Batch.objects.aggregate(total=Sum("remaining_qty"))
        .get("total")
        or 0
    )
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today).count()
    low_stock = Product.objects.filter(remaining_stock__lte=F("reorder_level"), is_active=True).count()
    near_expiry = Batch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=timezone.now() + timedelta(days=30),
    ).count()
    return {
        "dashboard_total_stock": total_stock,
        "dashboard_orders_today": orders_today,
        "dashboard_low_stock": low_stock,
        "dashboard_near_expiry": near_expiry,
    }
