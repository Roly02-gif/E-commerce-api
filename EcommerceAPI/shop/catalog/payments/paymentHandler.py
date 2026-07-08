from shop.catalog.orders.OrderModel import OrderModel
from shop.catalog.orders.OrderService import confirm_stock_reservations, release_stock_reservations
from shop.catalog.payments.paymentEvent import PaymentExpired, PaymentFailed, PaymentSucceeded
from shop.catalog.payments.paymentEvent import event_bus


def on_payment_succeeded(event: PaymentSucceeded):
    order = OrderModel.objects.get(id=event.order_id)
    order.status = OrderModel.OrderStatus.PAID
    order.save(update_fields=['status'])
    confirm_stock_reservations(order)


def on_payment_failed(event: PaymentFailed):
    order = OrderModel.objects.get(id=event.order_id)
    order.status = OrderModel.OrderStatus.FAILED
    order.save(update_fields=['status'])
    release_stock_reservations(order)


def on_payment_expired(event: PaymentExpired):
    order = OrderModel.objects.get(id=event.order_id)
    order.status = OrderModel.OrderStatus.CANCELLED
    order.save(update_fields=['status'])
    release_stock_reservations(order)


def register_handlers():
    event_bus.subscribe(PaymentSucceeded, on_payment_succeeded)
    event_bus.subscribe(PaymentFailed, on_payment_failed)
    event_bus.subscribe(PaymentExpired, on_payment_expired)