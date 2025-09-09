from django.db import models
from django.utils import timezone
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining
from .field_choices import DEGREE_CHOICES, BRANCH_CHOICES
 
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
    country_code = models.CharField(max_length=5, default="+91")
    phone = models.CharField(max_length=15, null=True)
    alternative_country_code = models.CharField(max_length=5, default="+91", blank=True)
    alternative_phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    
    # UG Details
    ugdegree = models.CharField(max_length=100, choices=DEGREE_CHOICES, null=True, blank=True)
    ugbranch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)
    ugpassout = models.IntegerField(choices=[(r, r) for r in range(2014, timezone.now().year + 6)], null=True, blank=True)
    ugpercentage = models.FloatField(null=True, blank=True)

    # PG Details
    pgdegree = models.CharField(max_length=100, choices=DEGREE_CHOICES, null=True, blank=True)
    pgbranch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)
    pgpassout = models.IntegerField(choices=[(r, r) for r in range(2014, timezone.now().year + 6)], null=True, blank=True)
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
    course_id = models.IntegerField(null=True, blank=True)
    trainer = models.ForeignKey('trainersdb.Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now, editable=False)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    course_percentage = models.FloatField(default=0)
    pl_required = models.BooleanField(default=False)
    source_of_joining = models.ForeignKey(SourceOfJoining, on_delete=models.SET_NULL, null=True, blank=True)
    mode_of_class = models.CharField(max_length=3, choices=MODE_CHOICES)
    week_type = models.CharField(max_length=2, choices=WEEK_TYPE)
    consultant = models.ForeignKey(Consultant, on_delete=models.SET_NULL, null=True)

    # Placement Status
    mock_interview_completed = models.BooleanField(default=False, blank=True, null=True)
    placement_session_completed = models.BooleanField(default=False, blank=True, null=True)
    certificate_issued = models.BooleanField(default=False, blank=True, null=True)
    onboardingcalldone = models.BooleanField(default=False, blank=True, null=True)
    interviewquestion_shared = models.BooleanField(default=False, blank=True, null=True)
    resume_template_shared = models.BooleanField(default=False, blank=True, null=True)

    @property
    def course(self):
        from coursedb.models import Course
        if self.course_id:
            try:
                return Course.objects.get(id=self.course_id)
            except Course.DoesNotExist:
                return None
        return None

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
