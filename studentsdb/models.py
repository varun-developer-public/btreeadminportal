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

    EMI_CHOICES = [
        ('NONE', 'None'),
        ('2', '2 EMI'),
        ('3', '3 EMI'),
        ('4', '4 EMI'),
    ]

    student_id = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=100)
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
    payment_account = models.ForeignKey('settingsdb.PaymentAccount', on_delete=models.SET_NULL, null=True, blank=True)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)
    gst_bill = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    emi_type = models.CharField(max_length=4, choices=EMI_CHOICES, default='NONE')

    emi_1_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_1_date = models.DateField(blank=True, null=True)

    emi_2_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_2_date = models.DateField(blank=True, null=True)

    emi_3_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_3_date = models.DateField(blank=True, null=True)

    emi_4_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_4_date = models.DateField(blank=True, null=True)

    total_pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.student_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            last_student = Student.objects.order_by('-id').first()
            if last_student and last_student.student_id:
                last_id = int(last_student.student_id.replace('BTR', ''))
                self.student_id = f'BTR{last_id + 1:04d}'
            else:
                self.student_id = 'BTR0001'
        super().save(*args, **kwargs)
