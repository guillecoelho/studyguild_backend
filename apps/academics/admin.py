from django.contrib import admin

from .models import Subject, SubjectGroup


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "abreviated_name", "institution", "created_at")
    list_filter = ("institution",)
    search_fields = ("name", "code", "abreviated_name")
    ordering = ("institution__name", "code")
    list_select_related = ("institution",)
    autocomplete_fields = ("institution",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50


@admin.register(SubjectGroup)
class SubjectGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "institution", "subjects_count", "created_at")
    list_filter = ("institution",)
    search_fields = ("name",)
    ordering = ("institution__name", "name")
    list_select_related = ("institution",)
    autocomplete_fields = ("institution",)
    filter_horizontal = ("subjects",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50

    @admin.display(description="Subjects", ordering=None)
    def subjects_count(self, obj):
        return obj.subjects.count()
