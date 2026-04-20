from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import User

from .models import StudentGroup, StudentGroupInvitation
from .serializers import (
    InvitableStudentSerializer,
    InvitationCreateSerializer,
    InvitationUpdateSerializer,
    StudentGroupInvitationSerializer,
    StudentGroupSerializer,
)


def _is_admin(user) -> bool:
    return getattr(user, "role", None) == "admin"


@extend_schema(tags=["student_groups"])
class StudentGroupViewSet(viewsets.ModelViewSet):
    serializer_class = StudentGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = StudentGroup.objects.select_related("creator_student").prefetch_related("students")
        if self.action in ("list",):
            qs = qs.filter(
                Q(creator_student=user) | Q(students=user)
            ).distinct()
        return qs.order_by("name")

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if not (obj.manageable_by(user) or obj.students.filter(id=user.id).exists()):
            raise PermissionDenied("You cannot access this student group")
        return obj

    def _resolved_institution_id(self, data):
        user = self.request.user
        if _is_admin(user):
            return data.get("institution_id") or user.institution_id
        return user.institution_id

    def create(self, request, *args, **kwargs):
        payload = request.data.get("student_group", request.data)
        institution_id = self._resolved_institution_id(payload)
        if not institution_id:
            return Response(
                {"errors": ["Student group institution is required"]},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        group = StudentGroup(
            name=serializer.validated_data["name"],
            institution_id=institution_id,
            creator_student=request.user,
        )
        try:
            group.full_clean()
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            )
        group.save()
        out = self.get_serializer(group)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.manageable_by(request.user):
            raise PermissionDenied("Only the group creator or an admin can manage this group")
        payload = request.data.get("student_group", request.data)
        serializer = self.get_serializer(group, data=payload, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.manageable_by(request.user):
            raise PermissionDenied("Only the group creator or an admin can manage this group")
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Leave a student group",
        description=(
            "Removes the current user from the group. Creator must provide "
            "`new_creator_student_id` (existing member, not self) to transfer ownership."
        ),
        responses=StudentGroupSerializer,
    )
    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        group = self.get_object()
        user = request.user
        if not group.students.filter(id=user.id).exists():
            raise PermissionDenied("Only group members can leave this group")

        if group.creator_student_id == user.id:
            next_id = request.data.get("new_creator_student_id") or request.data.get(
                "student_group", {}
            ).get("new_creator_student_id")
            if not next_id:
                return Response(
                    {"errors": ["Group creator must transfer ownership before leaving"]},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            try:
                next_creator = User.objects.get(pk=next_id)
            except User.DoesNotExist:
                return Response(
                    {"errors": ["New creator not found"]},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            if not group.students.filter(id=next_creator.id).exists():
                return Response(
                    {"errors": ["New creator must already belong to the group"]},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            if next_creator.id == user.id:
                return Response(
                    {"errors": ["New creator must be different from current creator"]},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            group.creator_student = next_creator
            group.save(update_fields=["creator_student"])

        group.students.remove(user)
        group.refresh_from_db()
        return Response(self.get_serializer(group).data)

    @extend_schema(
        summary="List students eligible for invitation",
        description="Students in the same institution, not already members, no pending invite. `q` filters by name/email, max 10 results.",
        responses=InvitableStudentSerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="invitable_students")
    def invitable_students(self, request, pk=None):
        group = self.get_object()
        if not group.manageable_by(request.user):
            raise PermissionDenied("Only the group creator or an admin can invite students")

        pending_ids = group.student_group_invitations.filter(status="pending").values_list(
            "invitee_id", flat=True
        )
        qs = (
            User.objects.filter(role=User.Role.STUDENT, institution_id=group.institution_id)
            .exclude(id__in=group.students.values_list("id", flat=True))
            .exclude(id__in=pending_ids)
        )
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
        qs = qs.order_by("first_name", "last_name")[:10]
        return Response(InvitableStudentSerializer(qs, many=True).data)


@extend_schema(tags=["student_group_invitations"])
class NestedInvitationCreateViewSet(
    mixins.CreateModelMixin, viewsets.GenericViewSet
):
    serializer_class = StudentGroupInvitationSerializer
    permission_classes = [IsAuthenticated]
    queryset = StudentGroupInvitation.objects.all()

    def create(self, request, *args, **kwargs):
        group_id = kwargs.get("student_group_pk")
        try:
            group = StudentGroup.objects.get(pk=group_id)
        except StudentGroup.DoesNotExist:
            return Response({"error": "Student group not found"}, status=status.HTTP_404_NOT_FOUND)

        if not group.manageable_by(request.user):
            raise PermissionDenied("Only the group creator or an admin can invite students")

        payload = request.data.get("student_group_invitation", request.data)
        create_serializer = InvitationCreateSerializer(data=payload)
        create_serializer.is_valid(raise_exception=True)
        invitee = create_serializer.validated_data["invitee_id"]

        invitation = StudentGroupInvitation(
            student_group=group,
            inviter=request.user,
            invitee=invitee,
            status=StudentGroupInvitation.Status.PENDING,
        )
        try:
            invitation.full_clean()
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            )
        try:
            invitation.save()
        except IntegrityError:
            return Response(
                {"errors": ["Invitee already has a pending invitation"]},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        out = StudentGroupInvitationSerializer(invitation, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["student_group_invitations"])
class StudentGroupInvitationViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    serializer_class = StudentGroupInvitationSerializer
    permission_classes = [IsAuthenticated]
    queryset = StudentGroupInvitation.objects.all()

    def get_queryset(self):
        return (
            StudentGroupInvitation.objects.select_related(
                "student_group", "inviter", "invitee"
            )
            .filter(invitee=self.request.user, status="pending")
            .order_by("-created_at")
        )

    def update(self, request, *args, **kwargs):
        invitation = StudentGroupInvitation.objects.select_related(
            "student_group", "inviter", "invitee"
        ).get(pk=kwargs["pk"])
        user = request.user
        if not (_is_admin(user) or invitation.invitee_id == user.id):
            raise PermissionDenied(
                "Only the invited student or an admin can update this invitation"
            )
        payload = request.data.get("student_group_invitation", request.data)
        update_serializer = InvitationUpdateSerializer(data=payload)
        update_serializer.is_valid(raise_exception=True)
        new_status = update_serializer.validated_data["status"]
        invitation.status = new_status
        invitation.save(update_fields=["status", "updated_at"])
        return Response(
            StudentGroupInvitationSerializer(
                invitation, context=self.get_serializer_context()
            ).data
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
