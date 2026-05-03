from rest_framework.viewsets import ModelViewSet

from shop.permissions import IsAdminOrReadOnly
from shop.catalog.categories.categorySerializer import CategorySerializer
from shop.catalog.categories.categoryModel import CategoryModel


class CategoryViewSet(ModelViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
