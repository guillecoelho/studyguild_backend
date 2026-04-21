from rest_framework.routers import DefaultRouter

from .views import InstitutionViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"institutions", InstitutionViewSet, basename="institution")

urlpatterns = router.urls
