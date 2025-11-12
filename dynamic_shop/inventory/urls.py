"""URLS pour les rapports d'inventaire."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("reports/expiry/", views.expiry_report, name="expiry-report"),
]
