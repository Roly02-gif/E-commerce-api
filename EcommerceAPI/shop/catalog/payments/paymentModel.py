import uuid
from django.db import models

from shop.catalog.payments.enums import PaymentProviderEnum
from shop.catalog.orders.OrderModel import OrderModel


class PaymentModel(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'Pending'
        SUCCEEDED = 'Succeeded'
        FAILED = 'Failed'
        EXPIRED = 'Expired'
    
    

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(OrderModel, related_name='payments', on_delete=models.PROTECT)
    provider = models.CharField(max_length=50, choices=PaymentProviderEnum.choices)   
    provider_reference = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.payment_status}"


class PaymentEventModel(models.Model):
    """Log brut de chaque event provider reçu — idempotence + audit."""
    id = models.CharField(max_length=255, primary_key=True)  # id natif du provider (evt_...)
    provider = models.CharField(max_length=50, choices=PaymentProviderEnum.choices)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)