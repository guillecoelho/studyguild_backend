from rest_framework import serializers

from apps.institutions.models import Institution

from .models import Subject, SubjectGroup


class SubjectSerializer(serializers.ModelSerializer):
    institution_id = serializers.PrimaryKeyRelatedField(
        source="institution", queryset=Institution.objects.all()
    )
    subject_group_ids = serializers.PrimaryKeyRelatedField(
        source="subject_groups", many=True, read_only=True
    )

    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "abreviated_name",
            "group_chat_link",
            "institution_id",
            "created_at",
            "updated_at",
            "subject_group_ids",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SubjectGroupSerializer(serializers.ModelSerializer):
    institution_id = serializers.PrimaryKeyRelatedField(
        source="institution", queryset=Institution.objects.all()
    )
    subject_ids = serializers.PrimaryKeyRelatedField(
        source="subjects", many=True, queryset=Subject.objects.all(), required=False
    )

    class Meta:
        model = SubjectGroup
        fields = [
            "id",
            "name",
            "institution_id",
            "created_at",
            "updated_at",
            "subject_ids",
        ]
        read_only_fields = ["created_at", "updated_at"]
