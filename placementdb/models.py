from django.db import models
from studentsdb.models import Student
from placementdrive.models import PlacementDrive

class Placement(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='placement')
    resume_link = models.FileField(upload_to='resumes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.student_id} - Placement"

class CompanyInterview(models.Model):
    placement = models.ForeignKey(Placement, on_delete=models.CASCADE, related_name='interviews')
    company = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='interviews',null=True)
    applying_for = models.CharField(max_length=255,null=True)
    interview_date = models.DateField()
    interview_time = models.TimeField()
    attended = models.BooleanField(default=False)

    def __str__(self):
        company_name = self.company.company_name if self.company else "N/A"
        return f"{company_name} interview for {self.placement.student.student_id}"
