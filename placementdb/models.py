from django.db import models
from studentsdb.models import Student

class Placement(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='placement')
    resume_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    feedback = models.TextField(blank=True)

    company_1 = models.CharField(max_length=255, blank=True)
    company_2 = models.CharField(max_length=255, blank=True)
    company_3 = models.CharField(max_length=255, blank=True)
    company_4 = models.CharField(max_length=255, blank=True)
    company_5 = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.student.student_id} - Placement"
