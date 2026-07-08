from django.db import transaction
from django.core.exceptions import ValidationError

from shop.catalog.orders.OrderModel import StockReservationModel
from shop.catalog.products.productModel import ProductVariantModel


class InsufficientStockError(ValidationError):
    pass


@transaction.atomic
def reserve_stock_for_order(order):
    for item in order.items.select_related('product_variant').all():
        if item.product_variant_id is None:
            continue 

        variant = ProductVariantModel.objects.select_for_update().get(id=item.product_variant_id)

        if variant.available_stock < item.quantity:
            raise InsufficientStockError(
                f"Insufficient stock for {variant.sku} "
                f"(requested: {item.quantity}, available: {variant.available_stock})"
            )

        variant.reserved += item.quantity
        variant.save(update_fields=['reserved'])

        StockReservationModel.objects.create(
            order_item=item,
            variant=variant,
            quantity=item.quantity,
            expires_at=StockReservationModel.default_expiry(),
        )


@transaction.atomic
def confirm_stock_reservations(order):
    reservations = StockReservationModel.objects.select_related('variant').filter(
        order_item__order=order, status=StockReservationModel.Status.RESERVED
    ).select_for_update()

    for reservation in reservations:
        variant = reservation.variant
        variant.stock_quantity = max(variant.stock_quantity - reservation.quantity, 0)
        variant.reserved = max(variant.reserved - reservation.quantity, 0)
        variant.save(update_fields=['stock', 'reserved'])

        reservation.status = StockReservationModel.Status.CONFIRMED
        reservation.save(update_fields=['status'])


@transaction.atomic
def release_stock_reservations(order):
    reservations = StockReservationModel.objects.select_related('variant').filter(
        order_item__order=order, status=StockReservationModel.Status.RESERVED
    ).select_for_update()

    for reservation in reservations:
        variant = reservation.variant
        variant.reserved = max(variant.reserved - reservation.quantity, 0)
        variant.save(update_fields=['reserved'])

        reservation.status = StockReservationModel.Status.RELEASED
        reservation.save(update_fields=['status'])