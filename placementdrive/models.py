from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from coursedb.models import Course

class Company(models.Model):
    company_code = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateField(default=timezone.now)
    portal = models.CharField(max_length=100)
    company_name = models.CharField(max_length=255)
    spoc = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} ({self.company_code})"

    def save(self, *args, **kwargs):
        if not self.company_code:
            last_company = Company.objects.all().order_by('id').last()
            if not last_company:
                self.company_code = 'COMP0001'
            else:
                last_code = last_company.company_code
                last_number = int(last_code.replace('COMP', ''))
                new_number = last_number + 1
                self.company_code = f'COMP{new_number:04d}'
        super().save(*args, **kwargs)

class ApplyingRole(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles')
    role_name = models.CharField(max_length=255)
    courses = models.ManyToManyField(Course)
    salary = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, editable=False)

    def __str__(self):
        course_names = ", ".join([course.course_name for course in self.courses.all()])
        return f"{self.role_name} ({course_names}) at {self.company.company_name}"