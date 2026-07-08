from django.urls import path
from rest_framework import routers

from shop.catalog.orders.OrderView import OrderViewSet
from shop.catalog.payments.paymentView import (
    CreatePaymentSessionView,
    PaymentCancelView,
    PaymentEventViewSet,
    PaymentSuccessView,
    PaymentViewSet,
    PaymentWebhookView,
)
from shop.catalog.products.productView import ProductVariantViewSet, ProductViewSet
from shop.catalog.users.userView import UserViewSet
from shop.catalog.categories.categoryView import CategoryViewSet

router = routers.SimpleRouter(trailing_slash=False)
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"users", UserViewSet, basename="user")
router.register(r"products", ProductViewSet, basename="product")
router.register('orders', OrderViewSet, basename='order')
router.register(r"payments", PaymentViewSet, basename='payment')
router.register(r"payments-event", PaymentEventViewSet, basename='payment-event')

variant_list = ProductVariantViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
variant_detail = ProductVariantViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'put': 'update',
    'delete': 'destroy',
})

urlpatterns = router.urls + [
    path('products/<int:product_pk>/variants', variant_list, name='product-variants-list'),
    path('products/<int:product_pk>/variants/<int:pk>', variant_detail, name='product-variants-detail'),
    path('orders/<uuid:order_id>/pay/', CreatePaymentSessionView.as_view()),
    path('orders/<uuid:order_id>/pay/success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('orders/<uuid:order_id>/pay/cancel/', PaymentCancelView.as_view(), name='payment-cancel'),
    path('webhook/<str:provider_name>/', PaymentWebhookView.as_view())
]
