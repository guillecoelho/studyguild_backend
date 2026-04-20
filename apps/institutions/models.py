"""Institution model. Mirrors Rails `Institution`."""
from django.db import models


class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "institutions"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
