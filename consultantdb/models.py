from django.db import models

class Consultant(models.Model):
    consultant_id = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    date_of_joining = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.consultant_id}"

    def save(self, *args, **kwargs):
        if not self.consultant_id:
            last_consultant = Consultant.objects.order_by('-id').first()
            if last_consultant and last_consultant.consultant_id:
                last_id = int(last_consultant.consultant_id.replace('CNS', ''))
                self.consultant_id = f'CNS{last_id + 1:03d}'
            else:
                self.consultant_id = 'CNS001'
        super().save(*args, **kwargs)
