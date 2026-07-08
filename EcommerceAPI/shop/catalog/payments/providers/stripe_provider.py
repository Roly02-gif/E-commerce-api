from decimal import Decimal
import json

import stripe
from django.conf import settings
from .base import PaymentProvider, PaymentSession, NormalizedEvent

stripe.api_key = settings.STRIPE_SECRET_KEY

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


class StripeProvider(PaymentProvider):
    name = 'STRIPE'

    def create_payment_session(self, order, success_url: str, cancel_url: str) -> PaymentSession:
        line_items = [{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': item.product_variant.product.name},
                'unit_amount': int(item.unit_price * 100),
            },
            'quantity': item.quantity,
        } for item in order.items.all()]

        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'order_id': str(order.id)},
        )

        return PaymentSession(
            provider_reference=session.id,
            redirect_url=session.url,
            raw=session,
        )

    def verify_and_parse_webhook(self, request) -> NormalizedEvent:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        data = event['data']['object']
        
        # print("DEBUG event.to_dict():", event.to_dict())  # debug temporaire
        # print("DEBUG data:", data)
    
        type_map = {
            'checkout.session.completed': 'payment.succeeded',
            'checkout.session.expired': 'payment.expired',
            'payment_intent.payment_failed': 'payment.failed',
        }
        normalized_type = type_map.get(event['type'], 'payment.unknown')
        order_id = data['metadata']['order_id'] if 'metadata' in data and 'order_id' in data['metadata'] else None
        # print(f"DEBUG : {order_id}---{normalized_type}")
        # raw_dict = json.loads(json.dumps(event.to_dict(), cls=DecimalEncoder))
        raw_dict = json.loads(str(event))
        # print(f"DEBUG : {raw_dict}--")
        
        return NormalizedEvent(
            event_type=normalized_type,
            provider_reference=data['id'],
            order_id=order_id,
            raw=raw_dict,
        )