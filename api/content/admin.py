from django.contrib import admin

from .models import Profile, Project


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # singleton: добавить можно только пока записи нет
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "project_type",
        "status",
        "is_published",
        "is_featured",
        "sort_order",
        "period_start",
    )
    list_filter = ("is_published", "project_type", "status")
    list_editable = ("is_published", "is_featured", "sort_order")
    search_fields = ("title", "slug", "tagline")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Что это", {"fields": ("title", "slug", "tagline", "project_type", "status")}),
        ("Резюме-контекст", {"fields": ("role", "org", "period_start", "period_end")}),
        ("Суть", {"fields": ("description_md", "stack", "highlights")}),
        ("Оформление и ссылки", {"fields": ("links", "cover", "uptime_monitor_slug")}),
        ("Публикация", {"fields": ("is_published", "is_featured", "sort_order")}),
    )
