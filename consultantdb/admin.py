from django.contrib import admin
from .models import Consultant, ConsultantProfile, Goal, Achievement

@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = ('consultant_id', 'name', 'phone_number', 'email', 'date_of_joining')
    search_fields = ('consultant_id', 'name', 'email', 'phone_number')
    list_filter = ('date_of_joining',)
    fields = ('consultant_id', 'name', 'country_code', 'phone_number', 'email', 'address', 'date_of_birth', 'date_of_joining')
    readonly_fields = ('consultant_id', 'date_of_joining')

@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'consultant')
    search_fields = ('user__email', 'user__name', 'consultant__name', 'consultant__consultant_id')

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('consultant', 'title', 'target_date', 'is_achieved')
    search_fields = ('title', 'consultant__name')
    list_filter = ('is_achieved', 'target_date')

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('consultant', 'title', 'date_achieved')
    search_fields = ('title', 'consultant__name')
    list_filter = ('date_achieved',)
