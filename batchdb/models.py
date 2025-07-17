from django.db import models
from trainersdb.models import Trainer

class Batch(models.Model):
    SLOT_CHOICES = [
        ('9-10.30', '9:00 AM - 10:30 AM'),
        ('10.30-12', '10:30 AM - 12:00 PM'),
        ('12-1.30', '12:00 PM - 1:30 PM'),
        ('3-4.30', '3:00 PM - 4:30 PM'),
        ('4.30-6', '4:30 PM - 6:00 PM'),
    ]
    batch_id = models.CharField(max_length=50, unique=True, blank=True)
    batch_name = models.CharField(max_length=100)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    students = models.ManyToManyField('studentsdb.Student', related_name='batches')

    def __str__(self):
        return self.batch_name

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
