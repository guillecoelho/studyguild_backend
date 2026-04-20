from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Subject, SubjectGroup
from .serializers import SubjectGroupSerializer, SubjectSerializer


@extend_schema(tags=["subjects"])
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().prefetch_related("subject_groups")
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@extend_schema(tags=["subject_groups"])
class SubjectGroupViewSet(viewsets.ModelViewSet):
    queryset = SubjectGroup.objects.all().prefetch_related("subjects")
    serializer_class = SubjectGroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
