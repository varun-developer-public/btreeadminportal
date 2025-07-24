from django.db import models
from trainersdb.models import Trainer

class Batch(models.Model):
    MODULE_CHOICES = [
        ('Python', 'Python'),
        ('Java', 'Java'),
        ('Spring Boot', 'Spring Boot'),
        ('Power BI', 'Power BI'),
        ('DA-Python', 'DA-Python'),
        ('UI/UX', 'UI/UX'),
        ('Dotnet', 'Dotnet'),
        ('C', 'C'),
        ('C++', 'C++'),
    ]

    BATCH_TYPE_CHOICES = [
        ('Weekday', 'Weekday'),
        ('Weekend', 'Weekend'),
    ]

    SLOT_CHOICES = [
        ('9-10.30', '9:00 AM - 10:30 AM'),
        ('10.30-12', '10:30 AM - 12:00 PM'),
        ('12-1.30', '12:00 PM - 1:30 PM'),
        ('3-4.30', '3:00 PM - 4:30 PM'),
        ('4.30-6', '4:30 PM - 6:00 PM'),
    ]

    batch_id = models.CharField(max_length=50, unique=True, blank=True)
    module_name = models.CharField(max_length=100, choices=MODULE_CHOICES,null=True)
    batch_type = models.CharField(max_length=10, choices=BATCH_TYPE_CHOICES, null=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=SLOT_CHOICES,null=True)
    students = models.ManyToManyField('studentsdb.Student', related_name='batches')

    def __str__(self):
        return f"{self.module_name} - {self.batch_type}"

    def save(self, *args, **kwargs):
        if not self.batch_id:
            last_batch = Batch.objects.order_by('-id').first()
            if last_batch and last_batch.batch_id and last_batch.batch_id.startswith('BAT_'):
                try:
                    last_id = int(last_batch.batch_id.split('_')[1])
                    self.batch_id = f'BAT_{last_id + 1:03d}'
                except (IndexError, ValueError):
                    self.batch_id = 'BAT_001'
            else:
                self.batch_id = 'BAT_001'
        super().save(*args, **kwargs)
