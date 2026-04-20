from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "institution",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "is_staff", "is_superuser", "institution")
    list_select_related = ("institution",)
    search_fields = ("email", "first_name", "last_name")
    autocomplete_fields = ("institution",)
    readonly_fields = ("last_login", "date_joined")
    date_hierarchy = "date_joined"
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "role",
                    "institution",
                    "career",
                    "description",
                    "profile_photo",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role"),
            },
        ),
    )
