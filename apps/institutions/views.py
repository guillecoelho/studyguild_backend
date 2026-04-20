from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Institution
from .serializers import InstitutionSerializer


@extend_schema(tags=["institutions"])
class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all().order_by("name")
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
