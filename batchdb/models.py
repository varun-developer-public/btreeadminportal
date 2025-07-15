from django.db import models
from trainersdb.models import Trainer

class Batch(models.Model):
    batch_id = models.CharField(max_length=50, unique=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    slot_timings = models.CharField(max_length=100)

    students = models.ManyToManyField('studentsdb.Student', related_name='batches')

    def __str__(self):
        return self.batch_id

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
