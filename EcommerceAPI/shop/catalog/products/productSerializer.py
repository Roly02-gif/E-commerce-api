# products/serializers.py
from rest_framework import serializers

from shop.catalog.products.productModel import ProductModel, ProductVariantModel


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantModel
        fields = [
            "id",
            "sku",
            "color",
            "size",
            "attributes",
            "price",
            "compare_price",
            "stock_quantity",
        ]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = ProductModel
        fields = ["id", "name", "slug", "description", "variants"]
