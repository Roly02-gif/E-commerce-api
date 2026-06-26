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

    def _get_category(self):
        category = self.context.get('category')
        if category is None and self.instance is not None:
            category = self.instance.category
        if category is None:
            category = self.initial_data.get('category') if hasattr(self, 'initial_data') else None
        if category is None and hasattr(self, 'validated_data'):
            category = self.validated_data.get('category')
        if isinstance(category, CategoryModel):
            return category
        if category is None:
            return None
        return CategoryModel.objects.filter(pk=category).first()

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Le nom du produit doit comporter au moins 2 caractères."
            )
        return value
    
    def validate_attributes(self, value):
        category = self._get_category()
        if category is None:
            return value

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
        if not isinstance(category, CategoryModel):
            category = CategoryModel.objects.filter(pk=category).first() if category is not None else None

        attributes = data.get('attributes', getattr(self.instance, 'attributes', {}) or {})
        if category is not None:
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