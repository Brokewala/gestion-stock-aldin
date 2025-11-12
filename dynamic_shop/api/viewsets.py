"""ViewSets REST pour DYNAMIC."""
from __future__ import annotations

from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dynamic_shop.inventory.models import Batch, Product, Supplier, Warehouse
from dynamic_shop.inventory.services import (
    PurchaseItem,
    adjust_stock,
    receive_purchase,
    transfer_stock,
)
from dynamic_shop.sales.models import Customer, Order, Payment
from dynamic_shop.sales.services import cancel_order, confirm_order, ship_order

from .filters import BatchFilter, OrderFilter, ProductFilter
from .permissions import IsStaffOrReadOnly
from .serializers import (
    BatchSerializer,
    CustomerSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("brand", "category")
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "flavor"]
    ordering_fields = ["name", "remaining_stock"]


class BatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Batch.objects.select_related("product", "warehouse")
    serializer_class = BatchSerializer
    filterset_class = BatchFilter
    permission_classes = [IsAuthenticated]


class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsStaffOrReadOnly]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name", "email"]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("customer", "warehouse").prefetch_related("items")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):  # type: ignore[override]
        order = self.get_object()
        try:
            confirm_order(order)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="ship")
    def ship(self, request, pk=None):  # type: ignore[override]
        order = self.get_object()
        try:
            ship_order(order)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):  # type: ignore[override]
        order = self.get_object()
        try:
            cancel_order(order)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("order")
    serializer_class = PaymentSerializer
    permission_classes = [IsStaffOrReadOnly]


class InventoryOperationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="receive")
    def receive(self, request):
        data = request.data
        supplier = data.get("supplier", "Inconnu")
        warehouse_id = data.get("warehouse")
        items = data.get("items", [])
        warehouse = Warehouse.objects.get(pk=warehouse_id)
        purchase_items = []
        for item in items:
            expiry = item.get("expiry_date")
            if expiry:
                try:
                    expiry = datetime.fromisoformat(expiry).date()  # type: ignore[assignment]
                except ValueError:
                    return Response(
                        {"detail": "Format de date invalide (attendu YYYY-MM-DD)."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            purchase_items.append(
                PurchaseItem(
                    product=Product.objects.get(sku=item["sku"]),
                    quantity=item["quantity"],
                    batch_code=item.get("batch_code"),
                    expiry_date=expiry,
                )
            )
        receive_purchase(supplier, purchase_items, warehouse, created_by=request.user)
        return Response({"status": "ok"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="transfer")
    def transfer(self, request):
        data = request.data
        product = Product.objects.get(sku=data["sku"])
        from_wh = Warehouse.objects.get(pk=data["from_warehouse"])
        to_wh = Warehouse.objects.get(pk=data["to_warehouse"])
        try:
            transfer_stock(
                product=product,
                quantity=data["quantity"],
                from_warehouse=from_wh,
                to_warehouse=to_wh,
                created_by=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "transferred"})

    @action(detail=False, methods=["post"], url_path="adjust")
    def adjust(self, request):
        data = request.data
        product = Product.objects.get(sku=data["sku"])
        warehouse = Warehouse.objects.get(pk=data["warehouse"])
        try:
            adjust_stock(
                product=product,
                warehouse=warehouse,
                quantity=data["quantity"],
                reason=data.get("reason", "Ajustement API"),
                created_by=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "adjusted"})
