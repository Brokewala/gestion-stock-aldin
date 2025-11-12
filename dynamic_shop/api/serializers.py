"""Serializers DRF pour les ressources DYNAMIC."""
from __future__ import annotations

from rest_framework import serializers

from dynamic_shop.inventory.models import Batch, Product, Supplier, Warehouse
from dynamic_shop.sales.models import Customer, Order, OrderItem, Payment


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "address", "description"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "phone", "address"]


class ProductSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="brand.name", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "brand",
            "category",
            "unit",
            "size_ml",
            "flavor",
            "remaining_stock",
            "reorder_level",
            "reorder_qty",
            "is_active",
        ]


class BatchSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source="product.sku", read_only=True)
    warehouse = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = Batch
        fields = ["id", "product", "batch_code", "expiry_date", "initial_qty", "remaining_qty", "warehouse"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "address"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="sku", queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price", "line_total", "batch"]
        read_only_fields = ["line_total", "batch"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "customer",
            "warehouse",
            "status",
            "total_amount",
            "created_at",
            "updated_at",
            "notes",
            "items",
        ]
        read_only_fields = ["code", "status", "total_amount", "created_at", "updated_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        for item in items_data:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
        order.refresh_total()
        return order


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "amount", "method", "paid_at"]
        read_only_fields = ["paid_at"]
