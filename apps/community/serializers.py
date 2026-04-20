from rest_framework import serializers

from .models import IssueReport, IssueReportImage, NewsletterEntry


def _full_name(user) -> str:
    if not user:
        return ""
    return " ".join(p for p in [user.first_name, user.last_name] if p)


class NewsletterEntrySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = NewsletterEntry
        fields = [
            "id",
            "title",
            "entry_type",
            "summary",
            "content",
            "published_at",
            "author_id",
            "author_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author_id", "created_at", "updated_at"]

    def get_author_name(self, obj) -> str:
        return _full_name(obj.author) or obj.author.email


class IssueReportImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = IssueReportImage
        fields = ["id", "url", "content_type", "byte_size", "created_at"]

    def get_url(self, obj) -> str | None:
        if not obj.image:
            return None
        try:
            return obj.image.url
        except Exception:
            return None


class IssueReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    images = IssueReportImageSerializer(many=True, read_only=True)

    class Meta:
        model = IssueReport
        fields = [
            "id",
            "title",
            "description",
            "status",
            "reporter_id",
            "reporter_name",
            "image_count",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reporter_id", "status", "created_at", "updated_at"]

    def get_reporter_name(self, obj) -> str:
        return _full_name(obj.reporter) or f"Student #{obj.reporter_id}"

    def get_image_count(self, obj) -> int:
        return len(obj.images.all())
