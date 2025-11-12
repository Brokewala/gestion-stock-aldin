"""Administration des ventes."""
from __future__ import annotations

from django.contrib import admin, messages

from .models import Customer, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "customer", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("code", "customer__name")
    inlines = [OrderItemInline]
    actions = ["mark_confirmed", "mark_shipped", "mark_cancelled"]

    @admin.action(description="Confirmer la commande")
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status=Order.Status.CONFIRMED)
        self.message_user(request, f"{updated} commande(s) confirmée(s)", level=messages.SUCCESS)

    @admin.action(description="Marquer comme expédiée")
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status=Order.Status.SHIPPED)
        self.message_user(request, f"{updated} commande(s) expédiée(s)", level=messages.SUCCESS)

    @admin.action(description="Annuler")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status=Order.Status.CANCELLED)
        self.message_user(request, f"{updated} commande(s) annulée(s)", level=messages.WARNING)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "method", "paid_at")
    list_filter = ("method", "paid_at")
    search_fields = ("order__code",)
