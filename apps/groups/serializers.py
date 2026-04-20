from rest_framework import serializers

from apps.users.models import User
from config.serializers import BusinessRulesMixin

from .models import StudentGroup, StudentGroupInvitation


def _full_name(user) -> str:
    if not user:
        return ""
    return " ".join(p for p in [user.first_name, user.last_name] if p)


class StudentGroupSerializer(BusinessRulesMixin, serializers.ModelSerializer):
    creator_student_name = serializers.SerializerMethodField()
    student_ids = serializers.PrimaryKeyRelatedField(
        source="students", many=True, read_only=True
    )
    students = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()

    class Meta:
        model = StudentGroup
        fields = [
            "id",
            "name",
            "institution_id",
            "creator_student_id",
            "created_at",
            "updated_at",
            "creator_student_name",
            "student_ids",
            "students",
            "can_manage",
        ]
        read_only_fields = [
            "institution_id",
            "creator_student_id",
            "created_at",
            "updated_at",
        ]

    def get_creator_student_name(self, obj) -> str:
        return _full_name(obj.creator_student)

    def get_students(self, obj) -> list[dict]:
        return [
            {
                "id": s.id,
                "name": _full_name(s),
                "career": s.career,
                "profile_photo_url": None,
            }
            for s in obj.students.all()
        ]

    def get_can_manage(self, obj) -> bool:
        user = self.context.get("request").user if self.context.get("request") else None
        return obj.manageable_by(user)


class StudentGroupInvitationSerializer(serializers.ModelSerializer):
    student_group_name = serializers.SerializerMethodField()
    inviter_name = serializers.SerializerMethodField()
    invitee_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentGroupInvitation
        fields = [
            "id",
            "student_group_id",
            "inviter_id",
            "invitee_id",
            "status",
            "created_at",
            "updated_at",
            "student_group_name",
            "inviter_name",
            "invitee_name",
        ]
        read_only_fields = [
            "student_group_id",
            "inviter_id",
            "invitee_id",
            "created_at",
            "updated_at",
        ]

    def get_student_group_name(self, obj) -> str | None:
        return obj.student_group.name if obj.student_group_id else None

    def get_inviter_name(self, obj) -> str:
        return _full_name(obj.inviter)

    def get_invitee_name(self, obj) -> str:
        return _full_name(obj.invitee)


class InvitableStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField()

    def get_full_name(self, obj) -> str:
        return _full_name(obj)


class InvitationCreateSerializer(serializers.Serializer):
    invitee_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class InvitationUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["accepted", "declined"])
