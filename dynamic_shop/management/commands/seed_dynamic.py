"""Commande de peuplement rapide pour DYNAMIC."""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from dynamic_shop.inventory.models import Brand, Category, Product, Supplier, Warehouse
from dynamic_shop.inventory.services import PurchaseItem, receive_purchase
from dynamic_shop.sales.models import Customer
from dynamic_shop.sales.services import OrderItemData, create_order, confirm_order


class Command(BaseCommand):
    help = "Peuple la base avec des données DYNAMIC de démonstration."

    @transaction.atomic
    def handle(self, *args, **options):
        brand, _ = Brand.objects.get_or_create(name="DYNAMIC", defaults={"description": "Énergie ultime"})
        category, _ = Category.objects.get_or_create(name="Boissons énergisantes")
        supplier, _ = Supplier.objects.get_or_create(name="Dynamic Supplier", defaults={"email": "supply@dynamic.bo"})
        warehouse, _ = Warehouse.objects.get_or_create(name="Principal", defaults={"address": "Zone Industrielle"})

        products = []
        catalog = [
            ("DYN-250-ORIG", "Original", 250, "Original"),
            ("DYN-330-MANG", "Mango", 330, "Mangue"),
            ("DYN-330-LIME", "Lime", 330, "Citron vert"),
            ("DYN-500-FRED", "Fraise-Raid", 500, "Fraise"),
            ("DYN-250-ZERO", "Zero Sugar", 250, "Sans sucre"),
        ]
        for sku, name, size, flavor in catalog:
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": f"DYNAMIC {name}",
                    "brand": brand,
                    "category": category,
                    "unit": "canette",
                    "size_ml": size,
                    "flavor": flavor,
                    "reorder_level": 200,
                    "reorder_qty": 500,
                },
            )
            products.append(product)

        items = [
            PurchaseItem(product=product, quantity=400, batch_code=f"{product.sku}-B1") for product in products
        ]
        receive_purchase(supplier.name, items, warehouse)

        customer, _ = Customer.objects.get_or_create(name="Super Marché DODO", defaults={"email": "achat@dodo.mg"})
        order = create_order(
            customer=customer,
            warehouse=warehouse,
            items=[
                OrderItemData(product=products[0], quantity=50, unit_price=Decimal("1800")),
                OrderItemData(product=products[1], quantity=30, unit_price=Decimal("1900")),
            ],
            notes="Commande de démonstration",
        )
        try:
            confirm_order(order)
        except ValueError:
            self.stdout.write(self.style.WARNING("Stock insuffisant pour confirmer la commande de démonstration."))
        self.stdout.write(self.style.SUCCESS("Base de données initialisée avec succès."))
        self.stdout.write("Identifiants d'exemple : créez un superuser avec 'python manage.py createsuperuser'.")
