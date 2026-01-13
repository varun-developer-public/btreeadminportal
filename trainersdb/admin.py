from django.contrib import admin
from .models import Trainer, TrainerProfile

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = (
        'trainer_id', 'name', 'phone_number', 'email', 'location',
        'years_of_experience', 'employment_type', 'mode_of_delivery',
        'availability', 'is_active', 'last_updated_at', 'last_updated_by'
    )
    search_fields = ('trainer_id', 'name', 'email', 'phone_number')
    list_filter = ('employment_type', 'location', 'is_active')
    filter_horizontal = ('stack',)
    readonly_fields = ('trainer_id', 'last_updated_at', 'last_updated_by')
    fields = (
        'trainer_id', 'name', 'country_code', 'phone_number', 'email', 'location', 'other_location',
        'years_of_experience', 'stack', 'employment_type', 'date_of_joining',
        'timing_slots', 'mode_of_delivery', 'availability', 'profile', 'demo_link',
        'commercials', 'is_active', 'last_updated_at', 'last_updated_by', 'last_update_remarks'
    )

@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'trainer')
    search_fields = ('user__email', 'user__name', 'trainer__name', 'trainer__trainer_id')
