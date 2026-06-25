from django.urls import path
from rest_framework import routers

from shop.catalog.products.productView import ProductVariantViewSet, ProductViewSet
from shop.catalog.users.userView import UserViewSet
from shop.catalog.categories.categoryView import CategoryViewSet

router = routers.SimpleRouter(trailing_slash=False)
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"users", UserViewSet, basename="user")
router.register(r"products", ProductViewSet, basename="product")

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
]
