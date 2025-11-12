"""Configuration de l'administration pour l'inventaire."""
from __future__ import annotations

from django.contrib import admin, messages
from django.db.models import F
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Batch, Brand, Category, Product, StockMovement, Supplier, Warehouse


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "barcode",
            "name",
            "brand__name",
            "category__name",
            "unit",
            "size_ml",
            "flavor",
            "reorder_level",
            "reorder_qty",
            "remaining_stock",
            "is_active",
        )


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "address")
    search_fields = ("name", "address")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ("name", "sku", "brand", "category", "remaining_stock", "reorder_level", "is_active")
    list_filter = ("brand", "category", "is_active")
    search_fields = ("name", "sku", "flavor")
    readonly_fields = ("remaining_stock", "created_at", "updated_at")
    fieldsets = (
        (
            "Informations principales",
            {
                "fields": (
                    "sku",
                    "barcode",
                    "name",
                    "brand",
                    "category",
                    "unit",
                    "size_ml",
                    "flavor",
                    "description",
                    "image",
                    "is_active",
                )
            },
        ),
        (
            "Pilotage du stock",
            {
                "fields": (
                    "reorder_level",
                    "reorder_qty",
                    "remaining_stock",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def mark_reorder(self, request, queryset):  # type: ignore[override]
        updated = queryset.update(reorder_level=F("remaining_stock"))
        self.message_user(request, f"{updated} produit(s) mis à jour", level=messages.SUCCESS)

    actions = ["mark_reorder"]


class BatchResource(resources.ModelResource):
    class Meta:
        model = Batch
        fields = (
            "id",
            "product__sku",
            "batch_code",
            "expiry_date",
            "initial_qty",
            "remaining_qty",
            "warehouse__name",
        )


@admin.register(Batch)
class BatchAdmin(ImportExportModelAdmin):
    resource_class = BatchResource
    list_display = ("batch_code", "product", "warehouse", "remaining_qty", "expiry_date")
    list_filter = ("warehouse", "product__brand", "product__category")
    search_fields = ("batch_code", "product__name", "product__sku")
    date_hierarchy = "expiry_date"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("movement_type", "product", "batch", "quantity", "from_warehouse", "to_warehouse", "created_at")
    list_filter = ("movement_type", "from_warehouse", "to_warehouse", "created_at")
    search_fields = ("product__name", "batch__batch_code", "reason")
    readonly_fields = ("product", "batch", "movement_type", "quantity", "from_warehouse", "to_warehouse", "reason")

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[override]
        return False


admin.site.site_header = "DYNAMIC Backoffice"
admin.site.site_title = "DYNAMIC Admin"
admin.site.index_title = "Tableau de bord"
