from django.db import models
from django.utils import timezone
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining
from .field_choices import DEGREE_CHOICES, BRANCH_CHOICES
import datetime

class CourseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
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
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, null=True)
    alternative_phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    
    # UG Details
    ugdegree = models.CharField(max_length=100, choices=DEGREE_CHOICES, null=True, blank=True)
    ugbranch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)
    ugpassout = models.IntegerField(choices=[(r, r) for r in range(2014, datetime.date.today().year + 1)], null=True, blank=True)
    ugpercentage = models.FloatField(null=True, blank=True)

    # PG Details
    pgdegree = models.CharField(max_length=100, choices=DEGREE_CHOICES, null=True, blank=True)
    pgbranch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)
    pgpassout = models.IntegerField(choices=[(r, r) for r in range(2014, datetime.date.today().year + 1)], null=True, blank=True)
    pgpercentage = models.FloatField(null=True, blank=True)

    # Work Status
    WORKING_STATUS_CHOICES = [('YES', 'Yes'), ('NO', 'No')]
    working_status = models.CharField(max_length=3, choices=WORKING_STATUS_CHOICES, default='NO')
    it_experience = models.CharField(max_length=10, choices=[('IT', 'IT'), ('NON-IT', 'Non-IT')], null=True, blank=True)
    
    # Course Status
    COURSE_STATUS_CHOICES = [
        ('YTS', 'Yet to Start'),
        ('IP', 'In Progress'),
        ('C', 'Completed'),
        ('R', 'Refund'),
        ('D', 'Discontinued'),
        ('H', 'Hold'),
        ('P', 'Placed')
    ]
    course_status = models.CharField(max_length=3, choices=COURSE_STATUS_CHOICES, default='YTS')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    trainer = models.ForeignKey('trainersdb.Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now, editable=False)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    course_percentage = models.FloatField(default=0)
    pl_required = models.BooleanField(default=False)
    source_of_joining = models.ForeignKey(SourceOfJoining, on_delete=models.SET_NULL, null=True)
    mode_of_class = models.CharField(max_length=3, choices=MODE_CHOICES)
    week_type = models.CharField(max_length=2, choices=WEEK_TYPE)
    consultant = models.ForeignKey(Consultant, on_delete=models.SET_NULL, null=True)

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
