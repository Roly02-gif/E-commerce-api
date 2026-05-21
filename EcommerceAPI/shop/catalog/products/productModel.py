import uuid

from django.db import models

from shop.catalog.categories.categoryModel import CategoryModel


class SizeModel(models.Model):
    class CategoryEnum(models.TextChoices):
        CLOTHING = "Clothing"
        SHOE = "Shoe"
        MONITOR = "Monitor"

    category = models.CharField(max_length=50, choices=CategoryEnum)
    name = models.CharField(max_length=20)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["category", "display_order"]
        unique_together = [["category", "name"]]


class ProductModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        CategoryModel, on_delete=models.PROTECT, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductVariantModel(models.Model):
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE, related_name="variants"
    )
    sku = models.CharField(max_length=50, unique=True, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.ForeignKey(SizeModel, on_delete=models.PROTECT, blank=True, null=True)

    # Attributs secondaires stockés en JSON (ex: "mémoire": "256GB", "matiere": "coton")
    attributes = models.JSONField(default=dict, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    stock_quantity = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._generate_sku()
        super().save(*args, **kwargs)

    def _generate_sku(self):
        name_component = (
            self.product.name[:3].upper()
            if len(self.product.name) >= 3
            else self.product.name.upper()
        )
        return f"SKU-{name_component}-{uuid.uuid4().hex[:12].upper()}"

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["product", "color", "size"]),
        ]
