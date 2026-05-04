from rest_framework.viewsets import ModelViewSet

from shop.catalog.products.productModel import ProductModel
from shop.catalog.products.productSerializer import ProductSerializer
from shop.permissions import IsAdminOrReadOnly


class ViewSet(ModelViewSet):
    queryset = ProductModel.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
