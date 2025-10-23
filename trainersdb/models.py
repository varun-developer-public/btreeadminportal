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
        ('Online/Offline', 'Online/Offline'),
    ]

    trainer_id = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5, default="+91")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=100, choices=TAMIL_NADU_LOCATIONS, blank=True, null=True)
    other_location = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.FloatField(default=0.0)
    stack = models.ManyToManyField(Course, blank=True)
    employment_type = models.CharField(max_length=2, choices=EMPLOYMENT_TYPE_CHOICES)
    date_of_joining = models.DateField(auto_now_add=True, null=True)
    timing_slots = models.JSONField(default=list, blank=True, null=True)
    mode_of_delivery = models.CharField(max_length=100, blank=True, null=True)
    availability = models.CharField(max_length=100, blank=True, null=True)
    profile = models.FileField(upload_to='trainer_profiles/', blank=True, null=True)
    demo_link = models.URLField(blank=True, null=True)
    commercials = models.JSONField(default=list, blank=True, null=True)
    is_active = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        if not self.trainer_id:
            last_trainer = Trainer.objects.order_by('-id').first()
            if last_trainer and last_trainer.trainer_id:
                last_id = int(last_trainer.trainer_id.replace('TRN', ''))
                self.trainer_id = f'TRN{last_id + 1:04d}'
            else:
                self.trainer_id = 'TRN0001'

        # Auto-populate mode_of_delivery and availability
        if self.timing_slots:
            modes = set(slot.get('mode') for slot in self.timing_slots)
            availabilities = set(slot.get('availability') for slot in self.timing_slots)

            mode_parts = []
            if 'Online' in modes:
                mode_parts.append('Online')
            if 'Offline' in modes:
                mode_parts.append('Offline')
            self.mode_of_delivery = '/'.join(sorted(mode_parts))

            availability_parts = []
            if 'WD' in availabilities:
                availability_parts.append('WD')
            if 'WE' in availabilities:
                availability_parts.append('WE')
            self.availability = '/'.join(sorted(availability_parts))
        else:
            self.mode_of_delivery = None
            self.availability = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer_id} - {self.name}"

from accounts.models import CustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class TrainerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='trainer_profile'
    )
    trainer = models.OneToOneField('Trainer', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.name}'s profile linked to {self.trainer.name}"

@receiver(post_save, sender='trainersdb.Trainer')
def create_or_update_trainer_profile(sender, instance, created, **kwargs):
    pass
