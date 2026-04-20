"""Reunions models: Reunion + ReunionMessage."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Reunion(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="reunions",
    )
    creator_student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_reunions",
    )
    student_group = models.ForeignKey(
        "groups.StudentGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reunions",
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    scheduled_for = models.DateTimeField()
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="reunions",
        db_table="reunions_students",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reunions"
        indexes = [
            models.Index(fields=["scheduled_for"], name="idx_reunions_scheduled_for"),
            models.Index(fields=["subject"], name="idx_reunions_subject"),
            models.Index(fields=["creator_student"], name="idx_reunions_creator"),
            models.Index(fields=["student_group"], name="idx_reunions_group"),
        ]

    @property
    def institution(self):
        return self.subject.institution if self.subject_id else None

    def clean(self):
        super().clean()
        errors = {}
        subject = getattr(self, "subject", None)
        creator = getattr(self, "creator_student", None)
        group = getattr(self, "student_group", None)

        if not self.scheduled_for:
            errors["scheduled_for"] = "can't be blank"
        if not self.visibility:
            errors["visibility"] = "can't be blank"

        if subject and creator and creator.institution_id != subject.institution_id:
            errors["creator_student"] = (
                "must belong to the same institution as the subject"
            )

        if self.visibility == self.Visibility.PRIVATE:
            if group is None:
                errors["student_group"] = "must be present for private reunions"
            else:
                if subject and group.institution_id != subject.institution_id:
                    errors["student_group"] = (
                        "must belong to the same institution as the subject"
                    )
                if (
                    creator is not None
                    and group.pk is not None
                    and not group.students.filter(pk=creator.pk).exists()
                    and group.creator_student_id != creator.pk
                ):
                    errors["creator_student"] = (
                        "must belong to the selected student group for private reunions"
                    )
        elif self.visibility == self.Visibility.PUBLIC:
            if group is not None:
                errors["student_group"] = "must be blank for public reunions"

        if errors:
            raise ValidationError(errors)

    def join_restriction_error_for(self, student):
        if student.institution_id != self.subject.institution_id:
            return "Student must belong to the same institution as the reunion subject"
        if self.visibility == self.Visibility.PRIVATE:
            if not self.student_group_id:
                return "Private reunions require a student group"
            if not self.student_group.students.filter(pk=student.pk).exists():
                return "Student must belong to the reunion student group"
        return None


class ReunionMessage(models.Model):
    reunion = models.ForeignKey(
        Reunion,
        on_delete=models.CASCADE,
        related_name="reunion_messages",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reunion_messages",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reunion_messages"
        indexes = [
            models.Index(fields=["reunion"], name="idx_rm_reunion"),
            models.Index(fields=["student"], name="idx_rm_student"),
            models.Index(fields=["created_at"], name="idx_rm_created_at"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if not self.content:
            errors["content"] = "can't be blank"
        reunion = getattr(self, "reunion", None)
        student = getattr(self, "student", None)
        if (
            reunion is not None
            and student is not None
            and reunion.pk is not None
            and not reunion.students.filter(pk=student.pk).exists()
        ):
            errors["student"] = "must be a participant of the reunion"
        if errors:
            raise ValidationError(errors)
