from rest_framework.viewsets import ModelViewSet

from django.shortcuts import get_object_or_404

from shop.catalog.products.productModel import ProductModel, ProductVariantModel
from shop.catalog.products.productSerializer import ProductCreateSerializer, ProductDetailSerializer, ProductUpdateSerializer, ProductVariantSerializer
from shop.permissions import IsAdminOrReadOnly


class ProductViewSet(ModelViewSet):
    queryset = ProductModel.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductDetailSerializer
        if self.action == 'create':
            return ProductCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        return ProductDetailSerializer



class ProductVariantViewSet(ModelViewSet):
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_product(self):
        return get_object_or_404(ProductModel, pk=self.kwargs['product_pk'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product'] = self.get_product()
        return context

    def get_queryset(self):
        return ProductVariantModel.objects.filter(product=self.get_product())

    def perform_create(self, serializer):
        serializer.save(product=self.get_product())