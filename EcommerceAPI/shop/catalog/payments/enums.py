from django.db import models

class PaymentProviderEnum(models.TextChoices):
        PAYPAL = 'PayPal'
        STRIPE = 'Stripe'