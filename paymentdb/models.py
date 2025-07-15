from django.db import models

class Payment(models.Model):
    EMI_CHOICES = [
        ('NONE', 'None'),
        ('2', '2 EMI'),
        ('3', '3 EMI'),
        ('4', '4 EMI'),
    ]

    student = models.OneToOneField('studentsdb.Student', on_delete=models.CASCADE)
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
        return f"Payment for {self.student.student_id} - {self.student.name}"
