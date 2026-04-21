from rest_framework.routers import DefaultRouter

from .views import SubjectGroupViewSet, SubjectViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"subject_groups", SubjectGroupViewSet, basename="subject-group")

urlpatterns = router.urls
