from django.db import models
from studentsdb.models import Student
from placementdrive.models import Company

class Placement(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='placement')
    resume_link = models.FileField(upload_to='resumes/', blank=True, null=True)
    std_professional_photo = models.ImageField(upload_to='professional_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    reason_for_inactive = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.student.student_id} - Placement"
    
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Placement.objects.get(pk=self.pk)
                if old_instance.resume_link and self.resume_link and self.resume_link != old_instance.resume_link:
                    old_instance.resume_link.delete(save=False)
            except Placement.DoesNotExist:
                pass
        super().save(*args, **kwargs)

class CompanyInterview(models.Model):
    ROUND_CHOICES = [
        ('virtual', 'Virtual'),
        ('aptitude', 'Aptitude'),
        ('technical', 'Technical'),
        ('hr', 'HR'),
        ('task', 'Task'),
    ]
    LOCATION_CHOICES = [
        ('chennai', 'Chennai'),
        ('bangalore', 'Bangalore'),
        ('hyderabad', 'Hyderabad'),
        ('others', 'Others'),
    ]

    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name='interviews')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='interviews',null=True)
    applying_for = models.CharField(max_length=255, null=True)
    interview_round = models.CharField(max_length=50, choices=ROUND_CHOICES, default='virtual')
    students = models.ManyToManyField(Student, related_name='interviews')
    location = models.CharField(max_length=255, choices=LOCATION_CHOICES, null=True)
    other_location = models.CharField(max_length=255, blank=True, null=True)
    interview_date = models.DateField()
    interview_time = models.TimeField()
    attended = models.BooleanField(default=False)
    selected = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        company_name = self.company.company_name if self.company else "N/A"
        return f"{company_name} interview for {self.placement.student.student_id}"
