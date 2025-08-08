from django.db import models
from django.conf import settings

class Consultant(models.Model):
    consultant_id = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5, default="+91")
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    date_of_joining = models.DateField(auto_now_add=True, null=True)

    class Meta:
        managed = True
        db_table = 'consultantdb_consultant'

    def __str__(self):
        return f"{self.name} - {self.consultant_id}"

    def save(self, *args, **kwargs):
        if not self.consultant_id:
            last_consultant = Consultant.objects.order_by('id').last()
            if last_consultant and last_consultant.consultant_id and last_consultant.consultant_id.startswith('CON'):
                last_id = int(last_consultant.consultant_id.replace('CON', ''))
                self.consultant_id = f'CON{last_id + 1:04d}'
            else:
                self.consultant_id = 'CON0001'
        super().save(*args, **kwargs)

class ConsultantProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consultant_profile')
    consultant = models.OneToOneField(Consultant, on_delete=models.CASCADE, db_constraint=False)

    def __str__(self):
        return f"Profile of {self.user.name}"

class Goal(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    description = models.TextField()
    target_date = models.DateField()
    is_achieved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Achievement(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_achieved = models.DateField()

    def __str__(self):
        return self.title
