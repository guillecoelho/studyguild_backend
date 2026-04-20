"""Custom User model.

Mirrors Rails `User` (Devise-backed): email as unique identifier, role
(student/admin), profile fields, optional institution FK.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    career = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    profile_photo = models.FileField(
        upload_to="profile_photos/", blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email

    def clean(self):
        super().clean()
        errors = {}
        if self.role == self.Role.STUDENT:
            if not self.first_name:
                errors["first_name"] = "can't be blank"
            if not self.last_name:
                errors["last_name"] = "can't be blank"
            if self.institution_id is None:
                errors["institution"] = "must exist"
        if self.career and len(self.career) > 120:
            errors["career"] = "is too long (maximum is 120 characters)"
        if self.description and len(self.description) > 2000:
            errors["description"] = "is too long (maximum is 2000 characters)"
        if errors:
            raise ValidationError(errors)
