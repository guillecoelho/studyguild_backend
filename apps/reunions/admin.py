from django.contrib import admin

from .models import Reunion, ReunionMessage


class ReunionMessageInline(admin.TabularInline):
    model = ReunionMessage
    extra = 0
    raw_id_fields = ("student",)
    readonly_fields = ("created_at",)
    fields = ("student", "content", "created_at")
    show_change_link = True


@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "subject",
        "creator_student",
        "visibility",
        "student_group",
        "scheduled_for",
        "participants_count",
    )
    list_filter = ("visibility", "subject__institution", "subject")
    search_fields = ("title", "description", "subject__name", "subject__code")
    ordering = ("-scheduled_for",)
    list_select_related = ("subject", "creator_student", "student_group")
    autocomplete_fields = ("subject", "creator_student", "student_group")
    filter_horizontal = ("students",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "scheduled_for"
    inlines = [ReunionMessageInline]
    list_per_page = 50

    @admin.display(description="Participants")
    def participants_count(self, obj):
        return obj.students.count()


@admin.register(ReunionMessage)
class ReunionMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "reunion", "student", "created_at")
    list_filter = ("reunion__visibility",)
    search_fields = ("content", "student__email", "reunion__title")
    ordering = ("-created_at",)
    list_select_related = ("reunion", "student")
    raw_id_fields = ("reunion", "student")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 100
