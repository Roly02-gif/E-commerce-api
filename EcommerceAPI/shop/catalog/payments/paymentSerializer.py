from rest_framework.serializers import Serializer, DecimalField, CharField

from shop.catalog.orders.OrderSerializer import OrderDetailSerializer
from shop.catalog.payments.paymentModel import PaymentEventModel, PaymentModel 

class PaymentSerializer(Serializer):
    order = OrderDetailSerializer(read_only=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = PaymentModel
        fields = ['order', 'provider', 'provider_reference', 'status', 'amount', 'date_created', 'date_updated']
        

class PaymentEventSerializer(Serializer):
    
    class Meta:
        model = PaymentEventModel
        fields = ['id', 'provider', 'event_type', 'payload', 'processed', 'received_at', 'processed_at']