from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase

from shop.catalog.categories.categoryModel import CategoryModel
from shop.catalog.products.productModel import ProductModel, ProductVariantModel


UserModel = get_user_model()


class ProductAndVariantApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = UserModel.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
        )
        self.category = CategoryModel.objects.create(
            name="Vêtements",
            attribute_schema={"brand": {"type": "string", "required": True}},
            variant_attribute_schema={"size": {"type": "string", "required": True}},
        )
        self.product_list_url = reverse("shop:product-list")

    def test_admin_can_create_product_with_variants(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "T-shirt",
            "description": "Un t-shirt confortable",
            "attributes": {"brand": "Nike"},
            "category": self.category.pk,
            "variants": [
                {
                    "attributes": {"size": "M"},
                    "price": "19.99",
                    "compare_price": "24.99",
                    "stock_quantity": 10,
                }
            ],
        }
        response = self.client.post(self.product_list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductModel.objects.count(), 1)
        product = ProductModel.objects.first()
        self.assertEqual(product.name, "T-shirt")
        self.assertEqual(product.variants.count(), 1)
        self.assertEqual(product.variants.first().attributes["size"], "M")
        self.assertEqual(response.data["variants"][0]["attributes"]["size"], "M")

    def test_create_product_with_invalid_variant_attributes_returns_400(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "T-shirt",
            "description": "Un t-shirt",
            "attributes": {"brand": "Nike"},
            "category": self.category.pk,
            "variants": [
                {
                    "attributes": {},
                    "price": "19.99",
                    "compare_price": "24.99",
                    "stock_quantity": 10,
                }
            ],
        }

        response = self.client.post(self.product_list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("variants", response.data)

    def test_product_detail_contains_variants(self):
        product = ProductModel.objects.create(
            name="Baskets",
            description="Chaussures de sport",
            attributes={"brand": "Adidas"},
            category=self.category,
        )
        ProductVariantModel.objects.create(
            product=product,
            attributes={"size": "42"},
            price="49.99",
            compare_price="59.99",
            stock_quantity=5,
        )

        detail_url = reverse("shop:product-detail", args=[product.pk])
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["variants"]), 1)
        self.assertEqual(response.data["variants"][0]["attributes"]["size"], "42")

    def test_admin_can_create_variant_for_existing_product(self):
        product = ProductModel.objects.create(
            name="Casquette",
            description="Casquette unisexe",
            attributes={"brand": "Puma"},
            category=self.category,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse("shop:product-variants-list", args=[product.pk])
        payload = {
            "attributes": {"size": "L"},
            "price": "15.00",
            "compare_price": "19.00",
            "stock_quantity": 7,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(product.variants.count(), 1)
        self.assertEqual(product.variants.first().attributes["size"], "L")

    def test_admin_can_update_variant_attributes(self):
        product = ProductModel.objects.create(
            name="Sweat",
            description="Sweat à capuche",
            attributes={"brand": "Champion"},
            category=self.category,
        )
        variant = ProductVariantModel.objects.create(
            product=product,
            attributes={"size": "S"},
            price="29.99",
            compare_price="34.99",
            stock_quantity=12,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse("shop:product-variants-detail", args=[product.pk, variant.pk])
        response = self.client.patch(url, {"attributes": {"size": "M"}}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        variant.refresh_from_db()
        self.assertEqual(variant.attributes["size"], "M")
