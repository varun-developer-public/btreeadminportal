from django.db import models
from django.utils import timezone
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining

class Student(models.Model):
    MODE_CHOICES = [
        ('ON', 'Online'),
        ('OFF', 'Offline'),
    ]

    WEEK_TYPE = [
        ('WD', 'Weekday'),
        ('WE', 'Weekend'),
    ]

    student_id = models.CharField(max_length=10, unique=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15)
    alternative_phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField()
    trainer = models.ForeignKey('trainersdb.Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    join_date = models.DateField(default=timezone.now)
    start_date = models.DateField(blank=True, null=True)
    tentative_end_date = models.DateField(blank=True, null=True)
    course_percentage = models.FloatField(default=0)
    pl_required = models.BooleanField(default=False)
    source_of_joining = models.ForeignKey(SourceOfJoining, on_delete=models.SET_NULL, null=True, blank=True)
    mode_of_class = models.CharField(max_length=3, choices=MODE_CHOICES)
    week_type = models.CharField(max_length=2, choices=WEEK_TYPE)
    consultant = models.ForeignKey(Consultant, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            last_student = Student.objects.order_by('-id').first()
            if last_student and last_student.student_id:
                last_id = int(last_student.student_id.replace('BTR', ''))
                self.student_id = f'BTR{last_id + 1:04d}'
            else:
                self.student_id = 'BTR0001'
        super().save(*args, **kwargs)
