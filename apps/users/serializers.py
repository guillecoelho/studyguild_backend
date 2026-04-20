from copy import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from apps.institutions.models import Institution

from .models import User


def _run_user_clean(user_instance):
    try:
        user_instance.clean()
    except DjangoValidationError as exc:
        if hasattr(exc, "message_dict"):
            raise serializers.ValidationError(exc.message_dict)
        raise serializers.ValidationError({"non_field_errors": exc.messages})


def _profile_photo_url(user: User) -> str | None:
    if not getattr(user, "profile_photo", None):
        return None
    try:
        return user.profile_photo.url
    except Exception:
        return None


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "description": user.description,
        "career": user.career,
        "institution_id": user.institution_id,
        "institution_name": user.institution.name if user.institution_id else None,
        "profile_photo_url": _profile_photo_url(user),
    }


class StudentSerializer(serializers.ModelSerializer):
    student_group_ids = serializers.PrimaryKeyRelatedField(
        source="student_groups", many=True, read_only=True
    )
    profile_photo_url = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)
    updated_at = serializers.DateTimeField(source="last_login", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "institution_id",
            "description",
            "career",
            "created_at",
            "updated_at",
            "student_group_ids",
            "profile_photo_url",
        ]

    def get_profile_photo_url(self, obj) -> str | None:
        return _profile_photo_url(obj)


class StudentWriteSerializer(serializers.ModelSerializer):
    institution_id = serializers.PrimaryKeyRelatedField(
        source="institution",
        queryset=Institution.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "institution_id",
            "description",
            "career",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        candidate = User(role=User.Role.STUDENT, **attrs)
        _run_user_clean(candidate)
        return attrs

    def create(self, validated_data):
        validated_data["role"] = User.Role.STUDENT
        password = self.context.get("default_password") or User.objects.make_random_password()
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StudentPublicProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    description = serializers.CharField()
    career = serializers.CharField()
    institution_name = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()

    def get_full_name(self, obj) -> str:
        parts = [p for p in [obj.first_name, obj.last_name] if p]
        return " ".join(parts)

    def get_institution_name(self, obj) -> str | None:
        return obj.institution.name if obj.institution_id else None

    def get_profile_photo_url(self, obj) -> str | None:
        return _profile_photo_url(obj)


@extend_schema_serializer(component_name="StudyGuildRegister")
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirmation = serializers.CharField(write_only=True, required=False)
    institution_id = serializers.PrimaryKeyRelatedField(
        source="institution",
        queryset=Institution.objects.all(),
        required=False,
        allow_null=True,
    )
    profile_photo = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirmation",
            "first_name",
            "last_name",
            "institution_id",
            "description",
            "career",
            "profile_photo",
        ]

    def validate(self, attrs):
        confirm = attrs.pop("password_confirmation", None)
        if confirm is not None and confirm != attrs.get("password"):
            raise serializers.ValidationError({"password_confirmation": "does not match"})
        scalar = {k: v for k, v in attrs.items() if k != "password"}
        candidate = User(role=User.Role.STUDENT, **scalar)
        _run_user_clean(candidate)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.STUDENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


@extend_schema_serializer(component_name="StudyGuildLogin")
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UpdateMeSerializer(serializers.ModelSerializer):
    institution_id = serializers.PrimaryKeyRelatedField(
        source="institution",
        queryset=Institution.objects.all(),
        required=False,
        allow_null=True,
    )
    profile_photo = serializers.FileField(required=False, allow_null=True)
    remove_profile_photo = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "institution_id",
            "description",
            "career",
            "profile_photo",
            "remove_profile_photo",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is None:
            return attrs
        candidate = copy(self.instance)
        for k, v in attrs.items():
            if k == "remove_profile_photo":
                continue
            setattr(candidate, k, v)
        _run_user_clean(candidate)
        return attrs

    def update(self, instance, validated_data):
        remove = validated_data.pop("remove_profile_photo", False)
        instance = super().update(instance, validated_data)
        if remove and instance.profile_photo:
            instance.profile_photo.delete(save=False)
            instance.profile_photo = None
            instance.save(update_fields=["profile_photo"])
        return instance
