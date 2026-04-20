from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.users.models import User

from .models import Reunion, ReunionMessage
from .serializers import ReunionMessageSerializer, ReunionSerializer


@extend_schema(
    tags=["reunions"],
    parameters=[
        OpenApiParameter("q", str, description="Text search in title/description/subject/group."),
        OpenApiParameter("subject_id", int),
        OpenApiParameter("creator_student_id", int),
        OpenApiParameter("student_group_id", int),
        OpenApiParameter("visibility", str, enum=["public", "private"]),
    ],
)
class ReunionViewSet(viewsets.ModelViewSet):
    serializer_class = ReunionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Reunion.objects.select_related(
            "subject", "student_group", "creator_student"
        ).prefetch_related("students", "reunion_messages")

        params = self.request.query_params
        q = params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(subject__name__icontains=q)
                | Q(subject__code__icontains=q)
                | Q(student_group__name__icontains=q)
            )
        if params.get("subject_id"):
            qs = qs.filter(subject_id=params["subject_id"])
        if params.get("creator_student_id"):
            qs = qs.filter(creator_student_id=params["creator_student_id"])
        if params.get("student_group_id"):
            qs = qs.filter(student_group_id=params["student_group_id"])
        if params.get("visibility"):
            qs = qs.filter(visibility=params["visibility"])

        return qs.order_by("scheduled_for").distinct()

    def perform_create(self, serializer):
        serializer.save()

    @extend_schema(
        summary="Join a reunion",
        description="Adds `student_id` to reunion participants. Enforces visibility + institution rules.",
        request={"application/json": {"type": "object", "properties": {"student_id": {"type": "integer"}}, "required": ["student_id"]}},
        responses=ReunionSerializer,
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        reunion = self.get_object()
        student_id = request.data.get("student_id")
        if not student_id:
            return Response(
                {"errors": ["student_id is required"]},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        try:
            student = User.objects.get(pk=student_id)
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        if student.role != User.Role.STUDENT:
            return Response(
                {"errors": ["Only students can join reunions"]},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        err = reunion.join_restriction_error_for(student)
        if err:
            return Response({"errors": [err]}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if not reunion.students.filter(id=student.id).exists():
            reunion.students.add(student)
        return Response(self.get_serializer(reunion).data)


@extend_schema(tags=["reunion_messages"])
class ReunionMessageViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    serializer_class = ReunionMessageSerializer

    def get_queryset(self):
        return (
            ReunionMessage.objects.select_related("student")
            .filter(reunion_id=self.kwargs.get("reunion_pk"))
            .order_by("created_at")
        )

    def create(self, request, *args, **kwargs):
        reunion_id = kwargs.get("reunion_pk")
        try:
            reunion = Reunion.objects.get(pk=reunion_id)
        except Reunion.DoesNotExist:
            return Response({"error": "Reunion not found"}, status=status.HTTP_404_NOT_FOUND)

        payload = request.data.get("reunion_message", request.data)
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        message = ReunionMessage(
            reunion=reunion,
            student=serializer.validated_data["student"],
            content=serializer.validated_data.get("content", ""),
        )
        try:
            message.full_clean()
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            )
        message.save()
        return Response(
            self.get_serializer(message).data, status=status.HTTP_201_CREATED
        )
