from django.contrib import admin
from .models import Batch, BatchStudent, BatchTransaction, TrainerHandover, TransferRequest

class BatchStudentInline(admin.TabularInline):
    model = BatchStudent
    extra = 0
    fields = ('student', 'is_active', 'activated_at', 'deactivated_at', 'update_remarks')
    readonly_fields = ('activated_at', 'deactivated_at')

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    inlines = [BatchStudentInline]
    list_display = (
        'batch_id', 'course', 'trainer', 'start_date', 'end_date', 'tentative_end_date',
        'batch_type', 'batch_status', 'get_slottime', 'hours_per_day',
        'batch_percentage', 'created_at', 'updated_at', 'created_by', 'updated_by'
    )
    search_fields = ('batch_id', 'course__course_name', 'trainer__name')
    list_filter = ('batch_status', 'batch_type', 'start_date', 'end_date', 'trainer')
    readonly_fields = ('batch_id', 'created_at', 'updated_at')
    fields = (
        'course', 'trainer', 'start_date', 'end_date', 'tentative_end_date',
        'batch_type', 'batch_status', 'start_time', 'end_time', 'days',
        'hours_per_day', 'batch_percentage', 'created_by', 'updated_by'
    )

@admin.register(BatchStudent)
class BatchStudentAdmin(admin.ModelAdmin):
    list_display = ('batch', 'student', 'is_active', 'activated_at', 'deactivated_at', 'update_remarks')
    search_fields = ('batch__batch_id', 'student__student_id', 'student__first_name', 'student__last_name')
    list_filter = ('is_active', 'activated_at', 'deactivated_at', 'batch')
    readonly_fields = ('activated_at', 'deactivated_at')
    fields = ('batch', 'student', 'is_active', 'activated_at', 'deactivated_at', 'update_remarks')

@admin.register(BatchTransaction)
class BatchTransactionAdmin(admin.ModelAdmin):
    list_display = ('batch', 'transaction_type', 'user', 'timestamp')
    search_fields = ('batch__batch_id', 'user__email', 'user__name')
    list_filter = ('transaction_type', 'timestamp')
    readonly_fields = ('timestamp',)
    fields = ('batch', 'transaction_type', 'user', 'details', 'timestamp', 'affected_students')
    filter_horizontal = ('affected_students',)

@admin.register(TrainerHandover)
class TrainerHandoverAdmin(admin.ModelAdmin):
    list_display = ('batch', 'from_trainer', 'to_trainer', 'status', 'requested_at', 'approved_at', 'handover_date')
    search_fields = ('batch__batch_id', 'from_trainer__name', 'to_trainer__name')
    list_filter = ('status', 'requested_at', 'approved_at')
    readonly_fields = ('requested_at', 'approved_at')
    fields = ('batch', 'from_trainer', 'to_trainer', 'status', 'remarks', 'handover_date', 'requested_at', 'approved_at')

@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ('from_batch', 'to_batch', 'status', 'requested_at', 'approved_at')
    search_fields = ('from_batch__batch_id', 'to_batch__batch_id')
    list_filter = ('status', 'requested_at', 'approved_at')
    readonly_fields = ('requested_at', 'approved_at')
    fields = ('from_batch', 'to_batch', 'students', 'requested_by', 'status', 'expires_at', 'approved_by', 'approved_at', 'remarks', 'requested_at')
    filter_horizontal = ('students',)
