from django.contrib import admin
from .models import Student, StudentConversation, ConversationMessage

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'student_id', 'first_name', 'last_name', 'phone', 'email', 'course_status',
        'course_id', 'trainer', 'enrollment_date', 'start_date', 'end_date',
        'course_percentage', 'pl_required', 'mode_of_class', 'week_type', 'consultant'
    )
    search_fields = ('student_id', 'first_name', 'last_name', 'email', 'phone')
    list_filter = ('course_status', 'mode_of_class', 'week_type', 'working_status', 'pl_required', 'consultant')
    readonly_fields = ('enrollment_date',)
    fields = (
        'student_id', 'first_name', 'last_name', 'country_code', 'phone',
        'alternative_country_code', 'alternative_phone', 'email', 'location',
        'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
        'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
        'working_status', 'it_experience',
        'course_status', 'course_id', 'trainer',
        'enrollment_date', 'start_date', 'end_date', 'course_percentage',
        'pl_required', 'source_of_joining', 'mode_of_class', 'week_type', 'consultant',
        'mock_interview_completed', 'placement_session_completed', 'certificate_issued',
        'onboardingcalldone', 'interviewquestion_shared', 'resume_template_shared'
    )

@admin.register(StudentConversation)
class StudentConversationAdmin(admin.ModelAdmin):
    list_display = ('student', 'created_at')
    search_fields = ('student__student_id', 'student__first_name', 'student__last_name', 'student__email', 'student__phone')

@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'sender_role', 'created_at')
    search_fields = ('message', 'sender__name', 'sender__email')
    list_filter = ('sender_role', 'created_at')
