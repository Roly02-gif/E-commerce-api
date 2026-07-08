import uuid

from django.db import models
from django.core.exceptions import ValidationError

from shop.catalog.utils.validators import validate_against_schema
from shop.catalog.categories.categoryModel import CategoryModel


class ProductModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    category = models.ForeignKey(
        CategoryModel, on_delete=models.PROTECT   )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def clean(self):
        schema = self.product.category.attribute_schema or {}
        errors = validate_against_schema(self.attributes, schema)
        if errors:
            raise ValidationError({'attributes': errors})


class ProductVariantModel(models.Model):
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE, related_name="variants"
    )
    sku = models.CharField(max_length=50, unique=True, blank=True)

    # Attributs secondaires stockés en JSON (ex: "size": "M", "mémoire": "256GB", "matiere": "coton")
    attributes = models.JSONField(default=dict, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)  

    @property
    def available_stock(self):
        return max(self.stock_quantity - self.reserved, 0)

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
    
    def clean(self):
        schema = self.product.category.variant_attribute_schema or {}
        errors = validate_against_schema(self.attributes, schema)
        if errors:
            raise ValidationError({'attributes': errors})

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["product"]),
        ]
