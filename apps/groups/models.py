"""Groups models: StudentGroup + StudentGroupInvitation."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class StudentGroup(models.Model):
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="student_groups",
    )
    creator_student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_student_groups",
    )
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="student_groups",
        db_table="student_groups_students",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_groups"
        constraints = [
            models.UniqueConstraint(
                "institution",
                Lower("name"),
                name="index_student_groups_on_institution_id_and_name",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "creator_student"], name="idx_stg_inst_creator"),
        ]

    def __str__(self) -> str:
        return self.name

    def manageable_by(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return self.creator_student_id == user.id or getattr(user, "role", None) == "admin"

    def clean(self):
        super().clean()
        errors = {}
        if not self.name:
            errors["name"] = "can't be blank"
        creator = getattr(self, "creator_student", None)
        if creator is None:
            errors["creator_student"] = "must exist"
        elif (
            getattr(creator, "role", None) != "admin"
            and self.institution_id is not None
            and creator.institution_id != self.institution_id
        ):
            errors["creator_student"] = (
                "must belong to the same institution as the student group"
            )
        if errors:
            raise ValidationError(errors)


class StudentGroupInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    student_group = models.ForeignKey(
        StudentGroup,
        on_delete=models.CASCADE,
        related_name="student_group_invitations",
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_student_group_invitations",
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_student_group_invitations",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_group_invitations"
        constraints = [
            models.UniqueConstraint(
                fields=["student_group", "invitee"],
                condition=Q(status="pending"),
                name="idx_student_group_invitations_pending_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["invitee"], name="idx_sgi_invitee"),
            models.Index(fields=["inviter"], name="idx_sgi_inviter"),
            models.Index(fields=["student_group"], name="idx_sgi_group"),
        ]

    def clean(self):
        super().clean()
        errors = {}

        def add(field, msg):
            errors.setdefault(field, []).append(msg)

        group = getattr(self, "student_group", None)
        inviter = getattr(self, "inviter", None)
        invitee = getattr(self, "invitee", None)

        if group is not None and inviter is not None and not group.manageable_by(inviter):
            add("inviter", "must be the student group creator or an admin")
        if invitee is not None and getattr(invitee, "role", None) != "student":
            add("invitee", "must be a student")
        if invitee is not None and inviter is not None and invitee.pk == inviter.pk:
            add("invitee", "must be different from inviter")
        if (
            invitee is not None
            and group is not None
            and group.pk is not None
            and group.students.filter(pk=invitee.pk).exists()
        ):
            add("invitee", "already belongs to this student group")
        if (
            invitee is not None
            and group is not None
            and invitee.institution_id != group.institution_id
        ):
            add("invitee", "must belong to the same institution as the student group")
        if (
            self.status == self.Status.PENDING
            and invitee is not None
            and group is not None
            and group.pk is not None
            and StudentGroupInvitation.objects.filter(
                student_group=group, invitee=invitee, status=self.Status.PENDING
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            add("invitee", "already has a pending invitation")
        if errors:
            raise ValidationError(errors)
