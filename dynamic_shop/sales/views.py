"""Vues simplifiées pour le module ventes."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Order


@login_required
def orders_overview(request):
    """Affiche la liste des commandes avec leur statut."""

    orders = Order.objects.select_related("customer").order_by("-created_at")[:50]
    return render(request, "sales/orders_overview.html", {"orders": orders})
