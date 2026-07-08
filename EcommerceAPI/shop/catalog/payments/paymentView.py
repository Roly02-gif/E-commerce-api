from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.conf import settings
from django.db import IntegrityError
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from shop.catalog.payments.paymentSerializer import PaymentSerializer, PaymentEventSerializer
from shop.catalog.payments.paymentTasks import process_payment_event
from shop.catalog.payments.paymentModel import PaymentEventModel, PaymentModel
from shop.catalog.orders.OrderModel import OrderModel
from .providers import get_provider

import logging

logger = logging.getLogger(__name__)

class PaymentViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'head']  # pas de création directe de paiement via l'API

    def get_queryset(self):
        return PaymentModel.objects.filter(order__buyer=self.request.user)

    def get_serializer_class(self):
        return PaymentSerializer
    
class PaymentEventViewSet(ModelViewSet):
    queryset = PaymentEventModel.objects.all()
    http_method_names = ['get', 'head']
    serializer_class = PaymentEventSerializer
    permission_classes = [permissions.IsAuthenticated]

class CreatePaymentSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        provider_name = request.data.get('provider', settings.DEFAULT_PAYMENT_PROVIDER)
        order = OrderModel.objects.prefetch_related('items__product_variant').filter(
            id=order_id, buyer=request.user, status=OrderModel.OrderStatus.PENDING
        )
        if not order.exists():
            return Response({'error': 'Order not found or not eligible for payment.'}, status=404)
        else:
            order = order.first()

        provider = get_provider(provider_name)
        session = provider.create_payment_session(
            order,
            success_url=f"http://localhost:8000/api/v1/orders/{order.id}/pay/success",
            cancel_url=f"http://localhost:8000/api/v1/orders/{order.id}/pay/cancel",
        )

        PaymentModel.objects.create(
            order=order,
            provider=provider.name,
            provider_reference=session.provider_reference,
            amount=order.total_price,
        )

        return Response({'redirect_url': session.redirect_url})
    
    # @action(detail=False, methods=['get'], url_path='success')
    # def success(self, request, order_id):
    #     return Response({'message': 'Payment succeeded for order {}'.format(order_id)})
    
    # @action(detail=False, methods=['get'], url_path='cancel')
    # def cancel(self, request, order_id):
    #     return Response({'message': 'Payment canceled for order {}'.format(order_id)})

class PaymentSuccessView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        return Response({'message': f'Payment succeeded for order {order_id}'})


class PaymentCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        return Response({'message': f'Payment canceled for order {order_id}'})



class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, provider_name):
        provider = get_provider(provider_name)

        try:
            normalized_event = provider.verify_and_parse_webhook(request)
        except Exception as e:
            logger.exception("Échec de vérification du webhook Stripe")
            return Response({'error': str(e)}, status=400)

        event_id = normalized_event.raw['id'] or normalized_event.provider_reference
        try:
            PaymentEventModel.objects.create(
                id=event_id,
                provider=provider.name,
                event_type=normalized_event.event_type,
                payload=normalized_event.raw,
            )
        except IntegrityError:
            return Response(status=200)  # déjà reçu, ack sans retraiter

        process_payment_event.delay(event_id)
        return Response(status=200)
