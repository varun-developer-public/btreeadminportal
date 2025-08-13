from django.db import models
from django.utils import timezone
from django.conf import settings
from trainersdb.models import Trainer
from coursedb.models import Course
from studentsdb.models import Student

import json
from datetime import datetime

class Batch(models.Model):
    STATUS_CHOICES = [
        ('YTS', 'Yet to Start'),
        ('IP', 'In Progress'),
        ('C', 'Completed'),
    ]
    
    BATCH_TYPE_CHOICES = [
        ('WD', 'Weekday'),
        ('WE', 'Weekend'),
        ('WDWE', 'Weekday & Weekend'),
        ('Hybrid', 'Hybrid'),
    ]

    batch_id = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches', null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    students = models.ManyToManyField(Student, related_name='batches', blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    batch_type = models.CharField(max_length=10, choices=BATCH_TYPE_CHOICES, default='WD')
    batch_status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='YTS')
    
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    days = models.JSONField(default=list)
    hours_per_day = models.PositiveIntegerField(default=2)
    batch_percentage = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_batches', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_batches', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.batch_id

    @property
    def get_slottime(self):
        if self.start_time and self.end_time:
            return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
        return "Not Set"

    def save(self, *args, **kwargs):
        if not self.batch_id:
            course_code = self.course.course_name.replace(" ", "")[:3].upper()
            trainer_initials = self.trainer.name.split(" ")[0][0].upper() if self.trainer else 'T'
            
            last_batch = Batch.objects.filter(
                course=self.course,
                trainer=self.trainer
            ).order_by('id').last()
            
            if last_batch and last_batch.batch_id:
                try:
                    last_num = int(last_batch.batch_id.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.batch_id = f"B-{course_code}-{trainer_initials}-{new_num:03d}"
            
        super().save(*args, **kwargs)
