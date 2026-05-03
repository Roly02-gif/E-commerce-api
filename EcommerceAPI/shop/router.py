from rest_framework import routers

from shop.catalog.categories.categoryView import CategoryViewSet

router = routers.SimpleRouter()
router.register(r"categories", CategoryViewSet, basename="category")
urlpatterns = router.urls
