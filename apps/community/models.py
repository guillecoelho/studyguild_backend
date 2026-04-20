"""Community models: NewsletterEntry + IssueReport."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGES_PER_REPORT = 5


def validate_image_size(file_obj):
    if file_obj.size > MAX_IMAGE_BYTES:
        raise ValidationError(
            f"must be smaller than {MAX_IMAGE_BYTES // (1024 * 1024)}MB"
        )


def validate_image_content_type(file_obj):
    content_type = getattr(file_obj, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError("must be a JPG, PNG, WEBP, or GIF file")


class NewsletterEntry(models.Model):
    class EntryType(models.TextChoices):
        NEWS = "news", "News"
        ARTICLE = "article", "Article"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="newsletter_entries",
    )
    title = models.CharField(max_length=160)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        default=EntryType.NEWS,
    )
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "newsletter_entries"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["author"], name="idx_ne_author"),
            models.Index(fields=["published_at"], name="idx_ne_published_at"),
            models.Index(fields=["entry_type", "published_at"], name="idx_ne_type_pub"),
        ]

    def save(self, *args, **kwargs):
        if self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class IssueReport(models.Model):
    class Status(models.IntegerChoices):
        OPEN = 0, "Open"
        IN_PROGRESS = 1, "In progress"
        RESOLVED = 2, "Resolved"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_reports",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=5000)
    status = models.IntegerField(choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "issue_reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reporter"], name="idx_ir_reporter"),
            models.Index(fields=["status"], name="idx_ir_status"),
        ]


def _issue_report_image_path(instance, filename):
    return f"issue_reports/{instance.issue_report_id}/{filename}"


class IssueReportImage(models.Model):
    issue_report = models.ForeignKey(
        IssueReport, on_delete=models.CASCADE, related_name="images"
    )
    image = models.FileField(
        upload_to=_issue_report_image_path,
        validators=[validate_image_size, validate_image_content_type],
    )
    content_type = models.CharField(max_length=100, blank=True)
    byte_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "issue_report_images"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["issue_report"], name="idx_iri_report"),
        ]
