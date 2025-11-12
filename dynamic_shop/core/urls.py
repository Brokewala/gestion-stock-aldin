"""Routes publiques et back-office simplifié."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("reports/low-stock/", views.low_stock_report, name="low-stock-report"),
]
