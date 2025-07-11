from django.db import models

class Trainer(models.Model):
    TRAINER_TYPE_CHOICES = [
        ('FT', 'Full Time'),
        ('FL', 'Freelancer'),
    ]

    trainer_id = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    trainer_type = models.CharField(max_length=2, choices=TRAINER_TYPE_CHOICES)
    stack = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        if not self.trainer_id:
            last_trainer = Trainer.objects.order_by('-id').first()
            if last_trainer and last_trainer.trainer_id:
                last_id = int(last_trainer.trainer_id.replace('TRN', ''))
                self.trainer_id = f'TRN{last_id + 1:04d}'
            else:
                self.trainer_id = 'TRN0001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer_id} - {self.name}"
