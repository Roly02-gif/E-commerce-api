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
        product = self.context.get('product') or self.instance.product
        schema = product.category.variant_attribute_schema or {}
        errors = validate_against_schema(value, schema)
        if errors:
            raise serializers.ValidationError(errors)
        return value


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True)
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
        fields = ["id", "name", "description", "category", "variants"]

    def create(self, validated_data):
        variants_data = validated_data.pop("variants", [])
        try:
            with transaction.atomic():
                product = ProductModel.objects.create(**validated_data)
                for variant in variants_data:
                    ProductVariantModel.objects.create(product=product, **variant)
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants", None)
        try:
            with transaction.atomic():
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()

                if variants_data is not None:
                    # Map existing variants by id for quick lookup
                    existing = {v.id: v for v in instance.variants.all()}
                    received_ids = []

                    for vdata in variants_data:
                        v_id = vdata.get("id", None)
                        if v_id:
                            received_ids.append(v_id)
                            variant = existing.get(v_id)
                            if variant:
                                for k, val in vdata.items():
                                    if k == "id":
                                        continue
                                    setattr(variant, k, val)
                                variant.save()
                            else:
                                # id provided but not found: create new linked to this product
                                data = {k: v for k, v in vdata.items() if k != "id"}
                                ProductVariantModel.objects.create(product=instance, **data)
                        else:
                            ProductVariantModel.objects.create(product=instance, **vdata)

                    # Delete variants that were omitted from payload
                    ids_to_delete = [vid for vid in existing.keys() if vid not in received_ids]
                    if ids_to_delete:
                        ProductVariantModel.objects.filter(id__in=ids_to_delete).delete()
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        return instance
