"""Modèles de gestion commerciale."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from dynamic_shop.inventory.models import Batch, Product, Warehouse


class Customer(models.Model):
    """Client B2B ou B2C."""

    name = models.CharField("Nom", max_length=150)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Order(models.Model):
    """Commande client avec gestion de statut."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        CONFIRMED = "CONFIRMED", "Confirmée"
        PAID = "PAID", "Payée"
        SHIPPED = "SHIPPED", "Expédiée"
        CANCELLED = "CANCELLED", "Annulée"

    code = models.CharField("Code", max_length=30, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField("Statut", max_length=12, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField("Montant total", max_digits=12, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return self.code

    def compute_totals(self) -> Decimal:
        """Calcule le montant total en additionnant les lignes."""

        total = self.items.aggregate(total=models.Sum("line_total"))
        value = total.get("total") or Decimal("0")
        self.total_amount = value
        return value

    def refresh_total(self) -> None:
        """Recalcule et sauvegarde le total."""

        value = self.compute_totals()
        self.save(update_fields=["total_amount", "updated_at"])

    @property
    def is_editable(self) -> bool:
        return self.status == self.Status.DRAFT

    def clean(self) -> None:
        if self.total_amount < 0:
            raise ValidationError("Le montant ne peut être négatif.")


class OrderItem(models.Model):
    """Ligne de commande associée à un lot de produit."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True)
    quantity = models.PositiveIntegerField("Quantité")
    unit_price = models.DecimalField("Prix unitaire", max_digits=10, decimal_places=2)
    line_total = models.DecimalField("Total ligne", max_digits=12, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
        unique_together = ("order", "product", "batch")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.order.code} - {self.product.name}"

    def clean(self) -> None:
        if self.quantity <= 0:
            raise ValidationError("La quantité doit être positive.")
        if self.unit_price < 0:
            raise ValidationError("Le prix ne peut être négatif.")

    def compute_total(self) -> Decimal:
        self.line_total = Decimal(self.quantity) * self.unit_price
        return self.line_total


class Payment(models.Model):
    """Paiements associés à une commande."""

    class Method(models.TextChoices):
        CASH = "CASH", "Espèces"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
        CARD = "CARD", "Carte"
        BANK = "BANK", "Virement bancaire"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField("Montant", max_digits=12, decimal_places=2)
    method = models.CharField("Méthode", max_length=20, choices=Method.choices)
    paid_at = models.DateTimeField("Payé le", default=timezone.now)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ("-paid_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"Paiement {self.amount} - {self.order.code}"

    def clean(self) -> None:
        if self.amount <= 0:
            raise ValidationError("Le montant du paiement doit être positif.")
