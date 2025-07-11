from django.db import models
from trainersdb.models import Trainer  # Trainer FK

class Batch(models.Model):
    batch_id = models.CharField(max_length=50, unique=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    slot_timings = models.CharField(max_length=100)

    # ManyToMany relationship to students
    students = models.ManyToManyField('studentsdb.Student', related_name='batches')

    def __str__(self):
        return self.batch_id
