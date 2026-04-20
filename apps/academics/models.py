"""Academics models: Subject, SubjectGroup. Mirror Rails tables 1:1."""
from django.db import models
from django.db.models.functions import Lower


class Subject(models.Model):
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abreviated_name = models.CharField(max_length=255, blank=True, null=True)
    group_chat_link = models.CharField(max_length=1024, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subjects"
        constraints = [
            models.UniqueConstraint(
                "institution",
                Lower("code"),
                name="index_subjects_on_institution_id_and_code",
            ),
        ]
        indexes = [
            models.Index(fields=["institution"], name="idx_subjects_institution"),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class SubjectGroup(models.Model):
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="subject_groups",
    )
    name = models.CharField(max_length=255)
    subjects = models.ManyToManyField(
        Subject,
        related_name="subject_groups",
        db_table="subject_groups_subjects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subject_groups"
        constraints = [
            models.UniqueConstraint(
                "institution",
                Lower("name"),
                name="index_subject_groups_on_institution_id_and_name",
            ),
        ]

    def __str__(self) -> str:
        return self.name
