"""Signals for reunions — mirror Rails `after_create` callback."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Reunion


@receiver(post_save, sender=Reunion)
def add_creator_to_participants(sender, instance, created, **kwargs):
    if not created or not instance.creator_student_id:
        return
    if not instance.students.filter(pk=instance.creator_student_id).exists():
        instance.students.add(instance.creator_student_id)
