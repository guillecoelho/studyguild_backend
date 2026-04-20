from django.contrib import admin

from .models import IssueReport, IssueReportImage, NewsletterEntry


@admin.register(NewsletterEntry)
class NewsletterEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "entry_type", "published_at")
    list_filter = ("entry_type",)
    search_fields = ("title", "content", "summary", "author__email")
    ordering = ("-published_at", "-created_at")
    list_select_related = ("author",)
    autocomplete_fields = ("author",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "published_at"
    list_per_page = 50


class IssueReportImageInline(admin.TabularInline):
    model = IssueReportImage
    extra = 0
    readonly_fields = ("content_type", "byte_size", "created_at")


@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "reporter", "status", "image_count", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "description", "reporter__email")
    ordering = ("-created_at",)
    list_select_related = ("reporter",)
    autocomplete_fields = ("reporter",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [IssueReportImageInline]
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("images")

    @admin.display(description="Images")
    def image_count(self, obj):
        return len(obj.images.all())
