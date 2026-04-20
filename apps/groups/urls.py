from django.urls import include, path
from rest_framework_nested import routers as nested_routers
from rest_framework.routers import DefaultRouter

from .views import (
    NestedInvitationCreateViewSet,
    StudentGroupInvitationViewSet,
    StudentGroupViewSet,
)

router = DefaultRouter()
router.register(r"student_groups", StudentGroupViewSet, basename="student-group")
router.register(
    r"student_group_invitations",
    StudentGroupInvitationViewSet,
    basename="student-group-invitation",
)

student_groups_router = nested_routers.NestedSimpleRouter(
    router, r"student_groups", lookup="student_group"
)
student_groups_router.register(
    r"student_group_invitations",
    NestedInvitationCreateViewSet,
    basename="nested-invitations",
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(student_groups_router.urls)),
]
