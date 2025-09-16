from django.db import models
from django.conf import settings
import os
from datetime import datetime

class SourceOfJoining(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PaymentAccount(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TransactionLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    table_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField()

    def __str__(self):
        return f"{self.timestamp} | {self.table_name} | {self.action}"




class UserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings')
    enable_2fa = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings for {self.user.email}"


class DBBackupImport(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    file_name = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to='db_backups/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    db_engine_used = models.CharField(max_length=50, blank=True, null=True)
    tables_affected = models.JSONField(default=dict, blank=True, null=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.status} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        if not self.file_name and self.uploaded_file:
            self.file_name = os.path.basename(self.uploaded_file.name)
        super().save(*args, **kwargs)
