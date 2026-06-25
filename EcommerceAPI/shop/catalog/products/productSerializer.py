from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError

from shop.catalog.utils.validators import validate_against_schema
from shop.catalog.categories.categoryModel import CategoryModel
from shop.catalog.products.productModel import (
    ProductModel,
    ProductVariantModel,
)


class ProductVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductVariantModel
        fields = [
            "id",
            "sku",
            "attributes",
            "price",
            "compare_price",
            "stock_quantity",
        ]
    
    def validate_attributes(self, value):
        product = self.context.get('product')
        schema = (product.category.variant_attribute_schema or {}) if product else {}
        errors = validate_against_schema(value, schema)
        if errors:
            raise serializers.ValidationError(errors)
        return value
    

# --- LECTURE (détail produit, avec variantes en lecture seule) ---
class ProductDetailSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=CategoryModel.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "attributes", "category", "variants", "is_active"]




class ProductCreateSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=CategoryModel.objects.all(), allow_null=True, required=False
    )

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Le nom du produit doit comporter au moins 2 caractères."
            )
        return value
    
    def validate_attributes(self, value):
        category = self.context.get('category') or self.instance.category
        schema = category.attribute_schema or {}
        errors = validate_against_schema(value, schema)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "attributes", "category", "variants", "is_active"]

    @transaction.atomic
    def create(self, validated_data):
        variants_data = validated_data.pop("variants", [])
        product = ProductModel.objects.create(**validated_data)
        schema = product.category.variant_attribute_schema or {}
        for variant in variants_data:
            errors = validate_against_schema(variant.get('attributes', {}), schema)
            if errors:
                raise serializers.ValidationError({'variants': errors})
            ProductVariantModel.objects.create(product=product, **variant)
        return product


# --- MODIFICATION (jamais de variantes ici) ---
class ProductUpdateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=CategoryModel.objects.all(), allow_null=True, required=False
    )
    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "attributes", "category", "is_active"]
        read_only_fields = ['id', 'date_created', 'date_updated']

    def validate(self, data):
        category = data.get('category', getattr(self.instance, 'category', None))
        attributes = data.get('attributes', getattr(self.instance, 'attributes', {}) or {})
        errors = validate_against_schema(attributes, category.attribute_schema or {})
        if errors:
            raise serializers.ValidationError({'attributes': errors})
        return data

    def to_internal_value(self, data):
        # bloque explicitement toute tentative d'envoyer 'variants' ici
        if 'variants' in data:
            raise serializers.ValidationError({
                'variants': "Les variantes ne se modifient pas via cet endpoint. "
                             "Utilisez /products/{id}/variants/{sku}/."
            })
        return super().to_internal_value(data)