"""Modèles liés à la gestion des stocks pour DYNAMIC."""
from __future__ import annotations

from datetime import date
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Brand(models.Model):
    """Marque commerciale, par défaut DYNAMIC."""

    name = models.CharField("Nom", max_length=100, unique=True)
    description = models.TextField("Description", blank=True)

    class Meta:
        verbose_name = "Marque"
        verbose_name_plural = "Marques"

    def __str__(self) -> str:  # pragma: no cover - représentation simple
        return self.name


class Category(models.Model):
    """Catégorie produit (boisson énergisante, pack, etc.)."""

    name = models.CharField("Nom", max_length=120)
    description = models.TextField("Description", blank=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        unique_together = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Warehouse(models.Model):
    """Entrepôt physique où sont stockées les boissons."""

    name = models.CharField("Nom", max_length=120, unique=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    description = models.TextField("Description", blank=True)

    class Meta:
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Supplier(models.Model):
    """Fournisseur de matières premières ou sous-traitant."""

    name = models.CharField("Nom", max_length=160)
    email = models.EmailField("Courriel", blank=True)
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Product(models.Model):
    """Produit DYNAMIC avec seuils d'alerte et informations marketing."""

    sku = models.CharField("SKU", max_length=50, unique=True)
    barcode = models.CharField("Code barre", max_length=64, blank=True)
    name = models.CharField("Nom", max_length=150)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    unit = models.CharField("Unité", max_length=50, help_text="Ex: canette, pack")
    size_ml = models.PositiveIntegerField("Volume (ml)")
    flavor = models.CharField("Saveur", max_length=120)
    image = models.ImageField("Visuel", upload_to="products/", blank=True, null=True)
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Actif", default=True)
    reorder_level = models.PositiveIntegerField("Seuil d'alerte", default=0)
    reorder_qty = models.PositiveIntegerField("Quantité de réapprovisionnement", default=0)
    remaining_stock = models.PositiveIntegerField("Stock disponible", default=0)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.sku})"

    @property
    def is_below_reorder(self) -> bool:
        """Indique si le stock courant est inférieur au seuil configuré."""

        return self.remaining_stock <= self.reorder_level


class Batch(models.Model):
    """Lot physique de production."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    batch_code = models.CharField("Code lot", max_length=100)
    expiry_date = models.DateField("Date de péremption", blank=True, null=True)
    initial_qty = models.PositiveIntegerField("Quantité initiale")
    remaining_qty = models.PositiveIntegerField("Quantité restante")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="batches")
    received_at = models.DateField("Date de réception", default=date.today)

    class Meta:
        verbose_name = "Lot"
        verbose_name_plural = "Lots"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "batch_code", "warehouse"],
                name="unique_batch_per_product_warehouse",
            )
        ]
        ordering = ("-received_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.product.name} - {self.batch_code}"

    def clean(self) -> None:
        """Empêche des quantités incohérentes."""

        if self.remaining_qty > self.initial_qty:
            raise ValidationError("La quantité restante ne peut excéder la quantité initiale.")
        if self.remaining_qty < 0:
            raise ValidationError("La quantité restante doit être positive.")

    @property
    def is_near_expiry(self) -> bool:
        """Retourne vrai si la péremption est inférieure à 30 jours."""

        if not self.expiry_date:
            return False
        return self.expiry_date <= timezone.now().date() + timezone.timedelta(days=30)


class StockMovement(models.Model):
    """Historique des mouvements de stock."""

    class MovementType(models.TextChoices):
        IN = "IN", "Entrée"
        OUT = "OUT", "Sortie"
        TRANSFER = "TRANSFER", "Transfert"
        ADJUSTMENT = "ADJUSTMENT", "Ajustement"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="movements", blank=True, null=True)
    movement_type = models.CharField("Type", max_length=20, choices=MovementType.choices)
    quantity = models.PositiveIntegerField("Quantité")
    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="movements_out",
        blank=True,
        null=True,
    )
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="movements_in",
        blank=True,
        null=True,
    )
    reason = models.CharField("Motif", max_length=255, blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        related_name="stock_movements",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.movement_type} - {self.product.name} ({self.quantity})"

    def clean(self) -> None:
        """Valide les contraintes métier sur les mouvements."""

        if self.quantity <= 0:
            raise ValidationError("La quantité doit être strictement positive.")
        if self.movement_type in {self.MovementType.OUT, self.MovementType.TRANSFER} and not self.from_warehouse:
            raise ValidationError("Un mouvement sortant doit préciser l'entrepôt d'origine.")
        if self.movement_type in {self.MovementType.IN, self.MovementType.TRANSFER} and not self.to_warehouse:
            raise ValidationError("Un mouvement entrant doit préciser l'entrepôt de destination.")
        if self.movement_type == self.MovementType.OUT and self.batch and self.quantity > self.batch.remaining_qty:
            raise ValidationError("Stock insuffisant sur le lot sélectionné.")

    def apply(self) -> None:
        """Applique la modification de stock correspondante."""

        from .services import apply_movement

        apply_movement(self)

    def save(self, *args: object, **kwargs: object) -> None:
        """Applique automatiquement la logique métier lors de l'enregistrement."""

        self.clean()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.apply()


def ensure_non_negative(value: int, message: str = "La quantité restante ne peut être négative.") -> None:
    """Valide qu'une quantité reste positive."""

    if value < 0:
        raise ValidationError(message)


def update_product_stock(product: Product) -> None:
    """Recalcule le stock total agrégé pour un produit donné."""

    aggregate = product.batches.aggregate(total=models.Sum("remaining_qty"))
    product.remaining_stock = aggregate.get("total") or 0
    product.save(update_fields=["remaining_stock", "updated_at"])


def reserve_stock(batch: Batch, quantity: int) -> None:
    """Réserve une quantité sur un lot sans dépasser le disponible."""

    ensure_non_negative(batch.remaining_qty - quantity)
    batch.remaining_qty -= quantity
    batch.save(update_fields=["remaining_qty"])
    update_product_stock(batch.product)


def release_stock(batch: Batch, quantity: int) -> None:
    """Libère une réservation sur un lot."""

    batch.remaining_qty += quantity
    if batch.remaining_qty > batch.initial_qty:
        batch.remaining_qty = batch.initial_qty
    batch.save(update_fields=["remaining_qty"])
    update_product_stock(batch.product)


def pick_batch(product: Product, quantity: int, warehouse: Optional[Warehouse] = None) -> Optional[Batch]:
    """Sélectionne le lot FIFO (plus proche de péremption) pour une quantité donnée."""

    qs = product.batches.filter(remaining_qty__gte=quantity)
    if warehouse is not None:
        qs = qs.filter(warehouse=warehouse)
    return qs.order_by(models.F("expiry_date").asc(nulls_last=True), "received_at").first()
