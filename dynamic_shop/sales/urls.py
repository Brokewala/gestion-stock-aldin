"""URLs module ventes."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("orders/", views.orders_overview, name="orders-overview"),
]
