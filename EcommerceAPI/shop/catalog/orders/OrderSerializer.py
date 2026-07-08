from rest_framework.serializers import CharField, DecimalField, IntegerField, ModelSerializer, Serializer, UUIDField, ValidationError
from shop.catalog.orders.OrderService import InsufficientStockError, reserve_stock_for_order
from shop.catalog.products.productModel import ProductModel, ProductVariantModel
from shop.catalog.orders.OrderModel import OrderItemModel, OrderModel
from django.db import transaction


class OrderItemInputSerializer(Serializer):
    product_variant_id = IntegerField()
    quantity = IntegerField(min_value=1)
        
        
class OrderCreateSerializer(ModelSerializer):
    items = OrderItemInputSerializer(many=True, write_only=True)
    class Meta:
        model = OrderModel
        fields = ['id', 'buyer', 'items', 'total_price', 'status', 'date_created']
        read_only_fields = ['id', 'buyer', 'total_price', 'status', 'date_created']
        
    def validate_items(self, value):
        if not value:
            raise ValidationError("Order must contain at least one item.")
        for item in value:
            product_variant_id = item.get('product_variant_id')
            quantity = item.get('quantity')

            # Validate product variant existence
            product_variant = ProductVariantModel.objects.filter(id=product_variant_id)
            if not product_variant.exists():
                raise ValidationError(f"Product variant with id {product_variant_id} does not exist.")

            # Validate stock availability
            if product_variant.first().stock_quantity < quantity:
                raise ValidationError(f"Not enough stock for variant {product_variant.first().sku}. Requested: {quantity}, Available: {product_variant.first().stock_quantity}")

        return value
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = self.initial_data.pop('items', [])
        order = OrderModel.objects.create(buyer=self.context['request'].user)
        for item_data in items_data:
            product_variant = ProductVariantModel.objects.get(id=item_data['product_variant_id'])

            OrderItemModel.objects.create(
                order=order,
                product_variant=product_variant,
                unit_price=product_variant.price,
                quantity=item_data['quantity'],
            )

        order.recalculate_total()
        order.save(update_fields=['total_price'])
        
        try:
            reserve_stock_for_order(order)
        except InsufficientStockError as e:
            raise ValidationError({'items': str(e)})

        return order
    
class OrderItemDetailSerializer(ModelSerializer):
    product_variant = IntegerField(source='product_variant.id', read_only=True)
    product_variant_sku = CharField(source='product_variant.sku', read_only=True)
    product_variant_price = DecimalField(max_digits=10, decimal_places=2, source='product_variant.price', read_only=True)
    product_name = CharField(source='product_variant.product.name', read_only=True)
    product_category = CharField(source='product_variant.product.category.name', read_only=True)
    product_description = CharField(source='product_variant.product.description', read_only=True)

    class Meta:
        model = OrderItemModel
        fields = ['id', 'product_variant', 'product_variant_sku', 'product_variant_price', 'product_name', 'product_category', 'product_description', 'quantity', 'unit_price']
        
class OrderDetailSerializer(ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    class Meta:
        model = OrderModel
        fields = ['id', 'status', 'total_price', 'items', 'date_created']
