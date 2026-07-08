from celery import shared_task
from django.db import transaction
from django.utils import timezone
from shop.catalog.payments.paymentModel import PaymentEventModel, PaymentModel
from shop.catalog.payments.paymentEvent import event_bus, PaymentSucceeded, PaymentFailed, PaymentExpired


@shared_task(bind=True, max_retries=3, default_retry_delay=10, queue="payments")
def process_payment_event(self, event_id):
    payment_event = PaymentEventModel.objects.get(id=event_id)
    if payment_event.processed:
        return
    if payment_event.event_type not in ('payment.succeeded', 'payment.failed', 'payment.expired'):
        payment_event.processed = True
        payment_event.processed_at = timezone.now()
        payment_event.save(update_fields=['processed', 'processed_at'])
        return
    
    try:
        with transaction.atomic():
            payment = PaymentModel.objects.select_for_update().get(
                provider=payment_event.provider,
                provider_reference=_extract_reference(payment_event),
            )

            if payment_event.event_type == 'payment.succeeded':
                payment.status = PaymentModel.PaymentStatus.SUCCEEDED
                payment.save(update_fields=['status'])
                event_bus.publish(PaymentSucceeded(order_id=str(payment.order_id)))

            elif payment_event.event_type == 'payment.failed':
                payment.status = PaymentModel.PaymentStatus.FAILED
                payment.save(update_fields=['status'])
                event_bus.publish(PaymentFailed(order_id=str(payment.order_id)))

            elif payment_event.event_type == 'payment.expired':
                payment.status = PaymentModel.PaymentStatus.EXPIRED
                payment.save(update_fields=['status'])
                event_bus.publish(PaymentExpired(order_id=str(payment.order_id)))

            payment_event.processed = True
            payment_event.processed_at = timezone.now()
            payment_event.save(update_fields=['processed', 'processed_at'])

    except PaymentModel.DoesNotExist:
        raise self.retry(exc=Exception(f"Payment introuvable pour event {event_id}"))


def _extract_reference(payment_event):
    # Chaque provider structure son payload différemment ;
    # à terme tu peux déléguer ça au provider lui-même si besoin
    data = payment_event.payload.get('data', {}).get('object', {})
    print(f"DATA EXTRACT REFERENCE : {data}")
    print(f"DATA ID REFERENCE : {data.get('id', '')}")
    return data.get('id', '')

