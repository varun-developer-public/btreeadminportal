from django.db import models
from coursedb.models import Course

class Trainer(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('FT', 'Full Time'),
        ('FL', 'Freelancer'),
    ]

    TAMIL_NADU_LOCATIONS = [
        ('Chennai', 'Chennai'),
        ('Coimbatore', 'Coimbatore'),
        ('Madurai', 'Madurai'),
        ('Tiruchirappalli', 'Tiruchirappalli'),
        ('Salem', 'Salem'),
        ('Tirunelveli', 'Tirunelveli'),
        ('Tiruppur', 'Tiruppur'),
        ('Vellore', 'Vellore'),
        ('Erode', 'Erode'),
        ('Thoothukudi', 'Thoothukudi'),
        ('Dindigul', 'Dindigul'),
        ('Thanjavur', 'Thanjavur'),
        ('Ranipet', 'Ranipet'),
        ('Sivakasi', 'Sivakasi'),
        ('Karur', 'Karur'),
        ('Udhagamandalam', 'Udhagamandalam'),
        ('Hosur', 'Hosur'),
        ('Nagercoil', 'Nagercoil'),
        ('Kanchipuram', 'Kanchipuram'),
        ('Kumarapalayam', 'Kumarapalayam'),
        ('Karaikkudi', 'Karaikkudi'),
        ('Neyveli', 'Neyveli'),
        ('Cuddalore', 'Cuddalore'),
        ('Tiruvannamalai', 'Tiruvannamalai'),
        ('Pollachi', 'Pollachi'),
        ('Rajapalayam', 'Rajapalayam'),
        ('Gudiyatham', 'Gudiyatham'),
        ('Pudukkottai', 'Pudukkottai'),
        ('Vaniyambadi', 'Vaniyambadi'),
        ('Ambur', 'Ambur'),
        ('Nagapattinam', 'Nagapattinam'),
        ('Others', 'Others'),
    ]

    MODE_CHOICES = [
        ('WE', 'Weekend'),
        ('WD', 'Weekday'),
        ('WEWD', 'Weekend/Weekday'),
        ('Hybrid', 'Hybrid'),
    ]

    AVAILABILITY_CHOICES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]

    trainer_id = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5, default="+91")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=100, choices=TAMIL_NADU_LOCATIONS, blank=True, null=True)
    other_location = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    stack = models.ManyToManyField(Course, blank=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, blank=True, null=True)
    availability = models.CharField(max_length=10, choices=AVAILABILITY_CHOICES, blank=True, null=True)
    employment_type = models.CharField(max_length=2, choices=EMPLOYMENT_TYPE_CHOICES)
    date_of_joining = models.DateField(auto_now_add=True, null=True)
    timing_slots = models.JSONField(default=list, blank=True, null=True)


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

