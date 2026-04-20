from django.contrib import admin

from .models import StudentGroup, StudentGroupInvitation


class StudentGroupInvitationInline(admin.TabularInline):
    model = StudentGroupInvitation
    extra = 0
    raw_id_fields = ("invitee", "inviter")
    readonly_fields = ("created_at", "updated_at")
    fields = ("invitee", "inviter", "status", "created_at")
    show_change_link = True


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "institution",
        "creator_student",
        "students_count",
        "created_at",
    )
    list_filter = ("institution",)
    search_fields = ("name", "creator_student__email")
    ordering = ("institution__name", "name")
    list_select_related = ("institution", "creator_student")
    autocomplete_fields = ("institution", "creator_student")
    filter_horizontal = ("students",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [StudentGroupInvitationInline]
    list_per_page = 50

    @admin.display(description="Members")
    def students_count(self, obj):
        return obj.students.count()


@admin.register(StudentGroupInvitation)
class StudentGroupInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_group",
        "invitee",
        "inviter",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "student_group__name",
        "invitee__email",
        "inviter__email",
    )
    ordering = ("-created_at",)
    list_select_related = ("student_group", "invitee", "inviter")
    raw_id_fields = ("student_group", "invitee", "inviter")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50
