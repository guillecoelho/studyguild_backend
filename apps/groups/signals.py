"""Signals for groups — mirror Rails `after_create` / `after_save` callbacks."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StudentGroup, StudentGroupInvitation


@receiver(post_save, sender=StudentGroup)
def add_creator_to_members(sender, instance, created, **kwargs):
    if not created or not instance.creator_student_id:
        return
    if not instance.students.filter(pk=instance.creator_student_id).exists():
        instance.students.add(instance.creator_student_id)


@receiver(post_save, sender=StudentGroupInvitation)
def add_invitee_when_accepted(sender, instance, **kwargs):
    if instance.status != StudentGroupInvitation.Status.ACCEPTED:
        return
    group = instance.student_group
    if not group.students.filter(pk=instance.invitee_id).exists():
        group.students.add(instance.invitee_id)
