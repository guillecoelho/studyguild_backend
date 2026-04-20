from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LoginView, LogoutView, MeView, RegisterView, StudentViewSet

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="student")

urlpatterns = [
    path("register", RegisterView.as_view(), name="api-register"),
    path("login", LoginView.as_view(), name="api-login"),
    path("logout", LogoutView.as_view(), name="api-logout"),
    path("me", MeView.as_view(), name="api-me"),
] + router.urls
