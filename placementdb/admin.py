from django.contrib import admin
from .models import Placement, CompanyInterview


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ("student", "is_active", "created_at", "updated_at")
    search_fields = ("student__student_id", "student__name")
    list_filter = ("is_active", "created_at", "updated_at")

    # allow deletion from admin
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.resume_link:
                obj.resume_link.delete(save=False)
            if obj.std_professional_photo:
                obj.std_professional_photo.delete(save=False)
            obj.delete()

