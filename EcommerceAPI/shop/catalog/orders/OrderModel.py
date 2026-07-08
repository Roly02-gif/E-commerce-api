from datetime import timedelta, timezone
import uuid

from django.db import models
from shop.models import UserModel
from shop.catalog.products.productModel import ProductModel, ProductVariantModel

class OrderModel(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'Pending'
        PAID = 'Paid'
        IN_DELIVERY = 'In Delivery'
        DELIVERED = 'Delivered'
        CANCELLED = 'Cancelled'
        FAILED = 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.username}"
    
    def recalculate_total(self):
        total = sum(item.unit_price * item.quantity for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])

class OrderItemModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariantModel, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.product.name} in Order {self.order.id}"
    


class StockReservationModel(models.Model):
    class Status(models.TextChoices):
        RESERVED = 'reserved'
        CONFIRMED = 'confirmed'
        RELEASED = 'released'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.OneToOneField(OrderItemModel, 
        related_name='reservation', on_delete=models.CASCADE
    )
    variant = models.ForeignKey(ProductVariantModel, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RESERVED)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def default_expiry():
        return timezone.now() + timedelta(minutes=30)