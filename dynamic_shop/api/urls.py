"""Déclarations des routes API."""
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .viewsets import (
    BatchViewSet,
    CustomerViewSet,
    InventoryOperationViewSet,
    OrderViewSet,
    PaymentViewSet,
    ProductViewSet,
    SupplierViewSet,
    WarehouseViewSet,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"batches", BatchViewSet, basename="batch")
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"inventory", InventoryOperationViewSet, basename="inventory-ops")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", obtain_auth_token, name="api-token"),
]
