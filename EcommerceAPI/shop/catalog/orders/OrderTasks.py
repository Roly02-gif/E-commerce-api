from datetime import timezone

from celery import shared_task

from shop.catalog.orders.OrderModel import OrderModel, StockReservationModel
from shop.catalog.orders.OrderService import release_stock_reservations


@shared_task
def release_expired_reservations():
    expired = StockReservationModel.objects.filter(
        status=StockReservationModel.Status.RESERVED,
        expires_at__lt=timezone.now(),
    ).select_related('order_item__order').distinct()

    orders_to_release = {r.order_item.order for r in expired}

    for order in orders_to_release:
        release_stock_reservations(order)
        if order.status == OrderModel.OrderStatus.PENDING:
            order.status = OrderModel.OrderStatus.CANCELLED
            order.save(update_fields=['status'])