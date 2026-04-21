from rest_framework import serializers

from apps.academics.models import Subject
from apps.groups.models import StudentGroup
from apps.users.models import User
from config.serializers import BusinessRulesMixin

from .models import Reunion, ReunionMessage


def _full_name(user) -> str:
    if not user:
        return ""
    return " ".join(p for p in [user.first_name, user.last_name] if p)


class ReunionSerializer(BusinessRulesMixin, serializers.ModelSerializer):
    subject_id = serializers.PrimaryKeyRelatedField(
        source="subject", queryset=Subject.objects.all()
    )
    student_group_id = serializers.PrimaryKeyRelatedField(
        source="student_group",
        queryset=StudentGroup.objects.all(),
        required=False,
        allow_null=True,
    )
    creator_student_id = serializers.PrimaryKeyRelatedField(
        source="creator_student", queryset=User.objects.all()
    )
    participant_student_ids = serializers.PrimaryKeyRelatedField(
        source="students", many=True, read_only=True
    )
    participant_student_names = serializers.SerializerMethodField()
    participant_students = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    student_group_name = serializers.CharField(
        source="student_group.name", read_only=True, allow_null=True
    )
    creator_student_name = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Reunion
        fields = [
            "id",
            "subject_id",
            "student_group_id",
            "visibility",
            "creator_student_id",
            "scheduled_for",
            "title",
            "description",
            "created_at",
            "updated_at",
            "participant_student_ids",
            "participant_student_names",
            "participant_students",
            "subject_name",
            "student_group_name",
            "creator_student_name",
            "messages_count",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_participant_student_names(self, obj) -> list[str]:
        return [_full_name(s) for s in obj.students.all()]

    def get_participant_students(self, obj) -> list[dict]:
        return [
            {
                "id": s.id,
                "name": _full_name(s),
                "career": s.career,
                "description": s.description,
                "profile_photo_url": s.profile_photo.url if s.profile_photo else None,
            }
            for s in obj.students.all()
        ]

    def get_creator_student_name(self, obj) -> str:
        return _full_name(obj.creator_student)

    def get_messages_count(self, obj) -> int:
        return obj.reunion_messages.count()


class ReunionMessageSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        source="student", queryset=User.objects.all()
    )
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ReunionMessage
        fields = [
            "id",
            "reunion_id",
            "student_id",
            "content",
            "created_at",
            "updated_at",
            "student_name",
        ]
        read_only_fields = ["reunion_id", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return _full_name(obj.student)
