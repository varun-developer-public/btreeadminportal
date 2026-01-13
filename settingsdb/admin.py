from django.contrib import admin
from .models import SourceOfJoining, PaymentAccount, TransactionLog, UserSettings, DBBackupImport

@admin.register(SourceOfJoining)
class SourceOfJoiningAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'table_name', 'object_id', 'action', 'timestamp')
    search_fields = ('table_name', 'object_id', 'user__email', 'user__name')
    list_filter = ('action', 'timestamp')
    readonly_fields = ('timestamp',)
    fields = ('user', 'table_name', 'object_id', 'action', 'timestamp', 'changes')

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'enable_2fa')
    search_fields = ('user__email', 'user__name')

@admin.register(DBBackupImport)
class DBBackupImportAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'status', 'uploaded_at', 'processed_at', 'imported_by', 'db_engine_used')
    search_fields = ('file_name', 'imported_by__email', 'imported_by__name')
    list_filter = ('status', 'uploaded_at', 'processed_at', 'db_engine_used')
    readonly_fields = ('uploaded_at', 'processed_at')
    fields = ('file_name', 'uploaded_file', 'uploaded_at', 'processed_at', 'status', 'error_message', 'imported_by', 'db_engine_used', 'tables_affected')
