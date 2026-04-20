from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import ReunionMessageViewSet, ReunionViewSet

router = DefaultRouter()
router.register(r"reunions", ReunionViewSet, basename="reunion")

reunions_router = nested_routers.NestedSimpleRouter(router, r"reunions", lookup="reunion")
reunions_router.register(r"reunion_messages", ReunionMessageViewSet, basename="reunion-messages")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(reunions_router.urls)),
]
