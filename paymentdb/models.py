from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from core.utils import timestamp_upload_to

class Payment(models.Model):
    EMI_CHOICES = [
        ('NONE', 'None'),
        ('1', '1 EMI'),
        ('2', '2 EMI'),
        ('3', '3 EMI'),
        ('4', '4 EMI'),
    ]

    payment_id = models.CharField(max_length=10, unique=True, editable=False, null=True, blank=True)
    student = models.OneToOneField('studentsdb.Student', on_delete=models.CASCADE)
    payment_account = models.ForeignKey('settingsdb.PaymentAccount', on_delete=models.SET_NULL, null=True)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)
    gst_bill = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    emi_type = models.CharField(max_length=4, choices=EMI_CHOICES, default='NONE')

    initial_payment_proof = models.ImageField(upload_to=timestamp_upload_to, null=True)
    
    # EMI fields with payment tracking

    # EMI 1
    emi_1_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_1_date = models.DateField(blank=True, null=True)
    emi_1_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_1_paid_date = models.DateField(blank=True, null=True)
    emi_1_proof = models.ImageField(upload_to=timestamp_upload_to, blank=True, null=True)
    emi_1_updated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_emi_1')

    # EMI 2
    emi_2_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_2_date = models.DateField(blank=True, null=True)
    emi_2_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_2_paid_date = models.DateField(blank=True, null=True)
    emi_2_proof = models.ImageField(upload_to=timestamp_upload_to, blank=True, null=True)
    emi_2_updated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_emi_2')

    # EMI 3
    emi_3_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_3_date = models.DateField(blank=True, null=True)
    emi_3_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_3_paid_date = models.DateField(blank=True, null=True)
    emi_3_proof = models.ImageField(upload_to=timestamp_upload_to, blank=True, null=True)
    emi_3_updated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_emi_3')

    # EMI 4
    emi_4_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_4_date = models.DateField(blank=True, null=True)
    emi_4_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    emi_4_paid_date = models.DateField(blank=True, null=True)
    emi_4_proof = models.ImageField(upload_to=timestamp_upload_to, blank=True, null=True)
    emi_4_updated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_emi_4')

    total_pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_total_pending(self):
        """Calculate the total pending amount from unpaid EMIs."""
        pending = self.total_fees - (self.amount_paid or 0)
        for i in range(1, 5):
            pending -= getattr(self, f'emi_{i}_paid_amount') or 0
        return pending

    def save(self, *args, **kwargs):
        # EMI overpayment validation
        for i in range(1, 5):
            emi_amount = getattr(self, f'emi_{i}_amount')
            paid_amount = getattr(self, f'emi_{i}_paid_amount')
            if emi_amount is not None and paid_amount is not None and paid_amount > emi_amount:
                raise ValueError(f"Paid amount for EMI {i} cannot exceed the due amount.")

        # Handle carry-forward logic before saving
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            for i in range(1, 5): # Iterate up to EMI 4
                # Check if a payment was made for this specific EMI in this transaction
                if (getattr(self, f'emi_{i}_paid_amount') or 0) > (getattr(original, f'emi_{i}_paid_amount') or 0):
                    
                    current_emi_amount = getattr(self, f'emi_{i}_amount') or 0
                    current_paid_amount = getattr(self, f'emi_{i}_paid_amount') or 0

                    # If it's underpaid, calculate deficit
                    if current_paid_amount < current_emi_amount:
                        deficit = current_emi_amount - current_paid_amount
                        
                        if i < 4: # Carry forward only if it's not EMI 4
                            next_emi_field = f'emi_{i+1}_amount'
                            next_emi_date_field = f'emi_{i+1}_date'
                            
                            # Get the original next EMI amount before any modifications
                            original_next_emi_amount = getattr(original, next_emi_field) or 0
                            
                            # Add the deficit to the next EMI
                            setattr(self, next_emi_field, original_next_emi_amount + deficit)

                            # If the next EMI didn't exist, set its due date and update emi_type
                            if not getattr(original, next_emi_field):
                                setattr(self, next_emi_date_field, (getattr(self, f'emi_{i}_paid_date') or timezone.now().date()) + relativedelta(months=1))
                                if i + 1 > int(self.emi_type):
                                    self.emi_type = str(i + 1)
                    
                    break # Assume only one EMI is paid per transaction.
        
        # Generate payment ID if not exists
        if not self.payment_id:
            last = Payment.objects.order_by('-id').first()
            next_id = int(last.payment_id.replace('PMT', '')) + 1 if last and last.payment_id else 1
            self.payment_id = f'PMT{next_id:04d}'

        # Validate EMI amounts based on EMI type
        max_emis = int(self.emi_type) if self.emi_type in ['1', '2', '3', '4'] else 0
        for i in range(1, 5):
            if i > max_emis:
                # Don't clear fields if they are being set by carry-forward
                if not getattr(self, f'emi_{i}_amount'):
                    setattr(self, f'emi_{i}_amount', None)
                    setattr(self, f'emi_{i}_date', None)
                    setattr(self, f'emi_{i}_paid_amount', None)
                    setattr(self, f'emi_{i}_paid_date', None)
                    if getattr(self, f'emi_{i}_proof'):
                        getattr(self, f'emi_{i}_proof').delete(save=False)
                    setattr(self, f'emi_{i}_proof', None)

        # Update total pending amount
        self.total_pending_amount = self.calculate_total_pending()
        super().save(*args, **kwargs)

    def get_payment_status(self):
        if self.total_pending_amount > 0:
            return "Pending"
        return "Paid"

    def __str__(self):
        return f"{self.payment_id} - {self.student}"

    def get_emi_range(self):
        """
        Returns a range of EMI numbers based on the emi_type.
        """
        if self.emi_type and self.emi_type != 'NONE':
            try:
                return range(1, int(self.emi_type) + 1)
            except (ValueError, TypeError):
                return []
        return []

    def get_next_payable_emi(self):
        paid_remaining = self.amount_paid or 0
        for i in range(1, 5):
            emi_amount = getattr(self, f'emi_{i}_amount') or 0
            if emi_amount == 0:
                continue
            emi_paid = getattr(self, f'emi_{i}_paid_amount') or 0
            remaining_for_emi = emi_amount - emi_paid
            if remaining_for_emi <= 0:
                continue
            if paid_remaining >= remaining_for_emi:
                paid_remaining -= remaining_for_emi
                continue
            return i
        return None

    def is_emi_fully_paid(self, emi_number):
        """Checks if a specific EMI is fully paid."""
        if not 1 <= emi_number <= 4:
            return False
            
        amount = getattr(self, f'emi_{emi_number}_amount')
        if not amount:  # If EMI doesn't exist
            return True
            
        paid_amount = getattr(self, f'emi_{emi_number}_paid_amount') or 0
        return paid_amount >= amount

    def can_edit_emi(self, emi_number):
        """Determines if a specific EMI can be edited based on payment status."""
        if not 1 <= emi_number <= 4:
            return False
            
        # First EMI can always be edited if it exists and is not fully paid
        if emi_number == 1:
            return bool(getattr(self, 'emi_1_amount')) and not self.is_emi_fully_paid(1)
            
        # For other EMIs, check if previous EMI exists and is fully paid
        prev_emi_amount = getattr(self, f'emi_{emi_number-1}_amount')
        if not prev_emi_amount or not self.is_emi_fully_paid(emi_number-1):
            return False
            
        # Current EMI must exist and not be fully paid
        current_emi_amount = getattr(self, f'emi_{emi_number}_amount')
        return bool(current_emi_amount) and not self.is_emi_fully_paid(emi_number)

class PendingPaymentRecord(models.Model):
    payment = models.OneToOneField('paymentdb.Payment', on_delete=models.CASCADE, related_name='pending_record')
    student = models.ForeignKey('studentsdb.Student', on_delete=models.CASCADE)
    student_code = models.CharField(max_length=10)
    student_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    batch_code = models.CharField(max_length=50, null=True, blank=True)
    batch_type = models.CharField(max_length=10, null=True, blank=True)
    course_id = models.IntegerField(null=True, blank=True)
    course_name = models.CharField(max_length=200, null=True, blank=True)
    course_status = models.CharField(max_length=3)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    next_emi_number = models.IntegerField(null=True, blank=True)
    next_emi_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    consultant_name = models.CharField(max_length=200, null=True, blank=True)
    trainer_name = models.CharField(max_length=200, null=True, blank=True)
    trainer_type = models.CharField(max_length=2, choices=[('FT', 'Full Time'), ('FL', 'Freelancer')], null=True, blank=True)
    course_percentage = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('Pending', 'Pending'), ('Paid', 'Paid')], default='Pending')
    feedback = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_pending_payments')
    edited_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_pending_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def refresh_from_sources(self):
        s = self.payment.student
        self.student = s
        self.student_code = s.student_id
        self.student_name = f"{s.first_name} {s.last_name or ''}"
        self.mobile = s.phone
        active_bs = s.batchstudent_set.filter(is_active=True).select_related('batch').first()
        self.batch_code = active_bs.batch.batch_id if active_bs else None
        self.batch_type = active_bs.batch.batch_type if active_bs else None
        self.course_id = s.course_id
        self.course_name = s.course.course_name if s.course else None
        self.course_status = s.course_status
        total_paid = self.payment.amount_paid or 0
        for i in range(1, 5):
            total_paid += getattr(self.payment, f'emi_{i}_paid_amount') or 0
        self.total_fee = self.payment.total_fees or 0
        self.amount_paid = total_paid
        self.pending_amount = self.payment.total_pending_amount or 0
        next_emi = self.payment.get_next_payable_emi()
        self.next_emi_number = next_emi
        self.next_emi_amount = getattr(self.payment, f'emi_{next_emi}_amount') if next_emi else None
        self.next_due_date = getattr(self.payment, f'emi_{next_emi}_date') if next_emi else None
        self.consultant_name = s.consultant.name if s.consultant else None
        self.trainer_name = (active_bs.batch.trainer.name if active_bs and active_bs.batch and active_bs.batch.trainer else (s.trainer.name if s.trainer else None))
        self.trainer_type = (active_bs.batch.trainer.employment_type if active_bs and active_bs.batch and active_bs.batch.trainer else (s.trainer.employment_type if s.trainer else None))
        self.course_percentage = s.course_percentage

from django.db.models.signals import post_save
from django.dispatch import receiver
from studentsdb.models import Student
from batchdb.models import Batch, BatchStudent

@receiver(post_save, sender=Payment)
def sync_pending_record(sender, instance, created, **kwargs):
    try:
        record = instance.pending_record
    except PendingPaymentRecord.DoesNotExist:
        record = None
    if instance.total_pending_amount > 0:
        if record is None:
            record = PendingPaymentRecord.objects.create(payment=instance, student=instance.student, course_status=instance.student.course_status)
        record.refresh_from_sources()
        record.status = 'Pending'
        updated_user = None
        for i in range(1, 5):
            u = getattr(instance, f'emi_{i}_updated_by')
            if u:
                updated_user = u
        record.edited_by = updated_user
        if record.created_by is None and updated_user:
            record.created_by = updated_user
        record.save()
    else:
        if record:
            record.refresh_from_sources()
            record.status = 'Paid'
            record.pending_amount = 0
            record.next_emi_number = None
            record.next_emi_amount = None
            record.next_due_date = None
            record.save()

@receiver(post_save, sender=Student)
def sync_pending_record_on_student_change(sender, instance, **kwargs):
    payments = Payment.objects.filter(student=instance)
    for p in payments:
        try:
            record = p.pending_record
        except PendingPaymentRecord.DoesNotExist:
            record = None
        if p.total_pending_amount > 0:
            if record is None:
                record = PendingPaymentRecord.objects.create(payment=p, student=p.student, course_status=p.student.course_status)
            record.refresh_from_sources()
            record.status = 'Pending'
            record.save()
        else:
            if record:
                record.refresh_from_sources()
                record.status = 'Paid'
                record.pending_amount = 0
                record.next_emi_number = None
                record.next_emi_amount = None
                record.next_due_date = None
                record.save()

@receiver(post_save, sender=BatchStudent)
def sync_pending_record_on_batchstudent_change(sender, instance, **kwargs):
    student = instance.student
    payments = Payment.objects.filter(student=student)
    for p in payments:
        try:
            record = p.pending_record
        except PendingPaymentRecord.DoesNotExist:
            record = None
        if p.total_pending_amount > 0:
            if record is None:
                record = PendingPaymentRecord.objects.create(payment=p, student=p.student, course_status=p.student.course_status)
            record.refresh_from_sources()
            record.status = 'Pending'
            record.save()
        else:
            if record:
                record.refresh_from_sources()
                record.status = 'Paid'
                record.pending_amount = 0
                record.next_emi_number = None
                record.next_emi_amount = None
                record.next_due_date = None
                record.save()

@receiver(post_save, sender=Batch)
def sync_pending_record_on_batch_change(sender, instance, **kwargs):
    active_students = instance.batchstudent_set.filter(is_active=True).select_related('student')
    for bs in active_students:
        student = bs.student
        payments = Payment.objects.filter(student=student)
        for p in payments:
            try:
                record = p.pending_record
            except PendingPaymentRecord.DoesNotExist:
                record = None
            if p.total_pending_amount > 0:
                if record is None:
                    record = PendingPaymentRecord.objects.create(payment=p, student=p.student, course_status=p.student.course_status)
                record.refresh_from_sources()
                record.status = 'Pending'
                record.save()
            else:
                if record:
                    record.refresh_from_sources()
                    record.status = 'Paid'
                    record.pending_amount = 0
                    record.next_emi_number = None
                    record.next_emi_amount = None
                    record.next_due_date = None
                    record.save()
