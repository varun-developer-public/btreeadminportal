from django.db import models
from django.utils import timezone
from django.conf import settings
from trainersdb.models import Trainer
from coursedb.models import Course
from studentsdb.models import Student

class Batch(models.Model):
    BATCH_STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
    ]

    batch_id = models.CharField(max_length=50, unique=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    students = models.ManyToManyField(Student, related_name='batches')
    
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    
    time_slot = models.CharField(max_length=50)
    batch_days = models.JSONField(default=list) 
    hours_per_day = models.PositiveIntegerField(default=2)
    
    batch_status = models.CharField(max_length=20, choices=BATCH_STATUS_CHOICES, default='In Progress')
    batch_percentage = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_batches', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_batches', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.batch_id} - {self.course.course_name if self.course else 'N/A'}"

    def save(self, *args, **kwargs):
        if not self.batch_id:
            course_code = self.course.course_name.replace(" ", "")[:2].upper()
            
            days = sorted([day.lower() for day in self.batch_days])
            if days == ['saturday', 'sunday']:
                week_type = 'WE'
            elif days == ['friday', 'monday', 'thursday', 'tuesday', 'wednesday']:
                week_type = 'WD'
            else:
                week_type = 'WEWD'

            trainer_id_num = self.trainer.trainer_id.replace('TRN', '')
            trainer_code = f"T{int(trainer_id_num)}"

            last_batch = Batch.objects.filter(
                course=self.course,
                trainer=self.trainer,
            ).order_by('-id').first()

            if last_batch and last_batch.batch_id:
                try:
                    last_id_num = int(last_batch.batch_id[-4:])
                    new_id = last_id_num + 1
                except (ValueError, IndexError):
                    new_id = 1
            else:
                new_id = 1
            
            batch_number = f"B{new_id:04d}"

            self.batch_id = f"{course_code}{week_type}{trainer_code}{batch_number}"

        super().save(*args, **kwargs)
