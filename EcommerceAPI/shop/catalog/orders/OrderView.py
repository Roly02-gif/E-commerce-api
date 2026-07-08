from rest_framework import viewsets, permissions

from shop.catalog.orders.OrderSerializer import OrderCreateSerializer, OrderDetailSerializer
from shop.catalog.orders.OrderModel import OrderModel


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']  # pas d'update/delete direct sur une commande

    def get_queryset(self):
        return OrderModel.objects.filter(buyer=self.request.user).prefetch_related('items__product_variant__product__category')

    def get_serializer_class(self):
        return OrderCreateSerializer if self.action == 'create' else OrderDetailSerializer