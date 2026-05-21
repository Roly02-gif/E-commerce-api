from rest_framework import routers

from shop.catalog.users.userView import UserViewSet
from shop.catalog.categories.categoryView import CategoryViewSet

router = routers.SimpleRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"users", UserViewSet, basename="user")
urlpatterns = router.urls
