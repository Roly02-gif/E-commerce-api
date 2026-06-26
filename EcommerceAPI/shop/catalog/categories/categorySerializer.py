from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from shop.catalog.categories.categoryModel import CategoryModel


class CategorySerializer(ModelSerializer):
    parent = PrimaryKeyRelatedField(
        allow_null=True, queryset=CategoryModel.objects.all(), required=False
    )

    class Meta:
        model = CategoryModel
        fields = ["id", "name", "parent"]
        depth = 1
