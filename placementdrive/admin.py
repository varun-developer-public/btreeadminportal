from django.contrib import admin
from .models import Company, ResumeSharedStatus, Interview, InterviewStudent

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_code', 'portal', 'progress', 'created_by')
    search_fields = ('company_name', 'company_code', 'email', 'mobile')
    list_filter = ('portal', 'progress', 'location', 'date')
    readonly_fields = ('company_code', 'created_by', 'created_at')

@admin.register(ResumeSharedStatus)
class ResumeSharedStatusAdmin(admin.ModelAdmin):
    list_display = ('company', 'status', 'role', 'resumes_shared', 'created_at', 'created_by')
    search_fields = ('company__company_name', 'role')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_by', 'created_at')

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('company', 'applying_role', 'interview_round', 'round_number', 'interview_date', 'created_by')
    search_fields = ('company__company_name', 'applying_role')
    list_filter = ('interview_round', 'venue', 'location', 'interview_date')
    readonly_fields = ('created_by', 'created_at')

@admin.register(InterviewStudent)
class InterviewStudentAdmin(admin.ModelAdmin):
    list_display = ('interview', 'student', 'status')
    search_fields = ('interview__company__company_name', 'student__first_name', 'student__last_name')
    list_filter = ('status',)