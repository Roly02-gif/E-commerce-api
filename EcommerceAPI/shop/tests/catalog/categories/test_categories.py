from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from shop.catalog.categories.categoryModel import CategoryModel


class CategoryViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Créer un admin et un utilisateur standard
        # self.admin_user = User.objects.create_superuser(
        #     username="admin", password="adminpass", email="admin@example.com"
        # )
        self.admin_user = User.objects.get(username="admin")
        self.regular_user = User.objects.create_user(
            username="user", password="userpass", email="user@example.com"
        )

        # Créer quelques catégories pour les tests
        self.category1 = CategoryModel.objects.create(name="Electronics")
        self.category2 = CategoryModel.objects.create(name="Books")

        # URLs (basées sur le router, ex: 'category-list', 'category-detail')
        # Adaptez le nom de la route si nécessaire (souvent 'categorie-list' etc.)
        self.list_url = reverse("shop:category-list")
        self.detail_url = lambda pk: reverse("shop:category-detail", args=[pk])

    # ---------- Tests de permissions (lecture seule pour tous) ----------

    def test_unauthenticated_user_can_list_categories(self):
        """Non authentifié peut lister les catégories"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # deux catégories créées

    def test_unauthenticated_user_can_retrieve_category(self):
        """Non authentifié peut voir une catégorie"""
        response = self.client.get(self.detail_url(self.category1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Electronics")

    def test_unauthenticated_user_cannot_create_category(self):
        """Non authentifié ne peut pas créer de catégorie"""
        data = {"name": "Clothing"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_update_category(self):
        """Non authentifié ne peut pas modifier une catégorie"""
        data = {"name": "Updated Name"}
        response = self.client.put(
            self.detail_url(self.category1.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_delete_category(self):
        """Non authentifié ne peut pas supprimer une catégorie"""
        response = self.client.delete(self.detail_url(self.category1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- Utilisateur standard (authentifié mais non-admin) ----------

    def test_authenticated_non_admin_can_list_categories(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_non_admin_can_retrieve_category(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.detail_url(self.category1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_non_admin_cannot_create_category(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {"name": "Clothing"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_non_admin_cannot_update_category(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {"name": "Hacked"}
        response = self.client.put(
            self.detail_url(self.category1.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_non_admin_cannot_delete_category(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(self.detail_url(self.category1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- Admin : tous droits ----------

    def test_admin_can_create_category(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "New Category"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CategoryModel.objects.count(), 3)
        self.assertEqual(response.data["name"], "New Category")

    def test_admin_can_update_category(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Updated Electronics"}
        response = self.client.put(
            self.detail_url(self.category1.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.name, "Updated Electronics")

    def test_admin_can_partial_update_category(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Partial Update"}
        response = self.client.patch(
            self.detail_url(self.category1.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.name, "Partial Update")

    def test_admin_can_delete_category(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(self.category1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CategoryModel.objects.count(), 1)  # reste category2

    # ---------- Tests du champ relationnel (PrimaryKeyRelatedField) ----------

    def test_create_category_with_parent_relation(self):
        """Admin peut créer une sous-catégorie en fournissant l'id du parent"""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Smartphones", "parent": self.category1.pk}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["parent"], self.category1.pk)
        new_cat = CategoryModel.objects.get(name="Smartphones")
        self.assertEqual(new_cat.parent, self.category1)

    def test_create_category_without_parent_optional(self):
        """Le champ parent est optionnel : création sans parent possible"""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Standalone"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(
            response.data.get("parent")
        )  # ou vérifier que la clé n'existe pas

    def test_create_category_with_null_parent(self):
        """Envoyer explicitement null pour le parent (si allow_null=True)"""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "No Parent", "parent": None}
        response = self.client.post(self.list_url, data, format="json")
        # selon votre sérialiseur, peut être 201 ou 400 si allow_null non activé
        # On suppose allow_null=True
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data.get("parent"))

    def test_update_category_parent(self):
        """Admin peut changer le parent d'une catégorie"""
        self.client.force_authenticate(user=self.admin_user)
        # Créer une troisième catégorie
        cat3 = CategoryModel.objects.create(name="Toys")
        data = {"parent": self.category2.pk}
        response = self.client.patch(self.detail_url(cat3.pk), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat3.refresh_from_db()
        self.assertEqual(cat3.parent, self.category2)

    def test_invalid_parent_id_returns_400(self):
        """Si l'id parent n'existe pas, DRF doit renvoyer 400 Bad Request"""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Bad", "parent": 9999}  # id inexistant
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent", response.data)
