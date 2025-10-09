from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from trainersdb.models import Trainer
from coursedb.models import Course, CourseCategory
from studentsdb.models import Student
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from datetime import datetime
import string
from django.contrib.postgres.fields import JSONField as PostgresJSONField

# Use JSONField based on database backend
try:
    from django.db.models import JSONField
except ImportError:
    # For Django versions < 3.1
    JSONField = PostgresJSONField

class Batch(models.Model):
    STATUS_CHOICES = [
        ('YTS', 'Yet to Start'),
        ('IP', 'In Progress'),
        ('C', 'Completed'),
    ]
    
    BATCH_TYPE_CHOICES = [
        ('WD', 'Weekday'),
        ('WE', 'Weekend'),
        ('WDWE', 'Weekday & Weekend'),
        ('Hybrid', 'Hybrid'),
    ]

    batch_id = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches', null=True, blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    students = models.ManyToManyField(Student, through='BatchStudent', related_name='batches', blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    batch_type = models.CharField(max_length=10, choices=BATCH_TYPE_CHOICES, default='WD')
    batch_status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='YTS')
    
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    days = models.JSONField(default=list)
    hours_per_day = models.DecimalField(
        max_digits=4,        
        decimal_places=2,   
        default=1.50,
        validators=[MinValueValidator(0.5), MaxValueValidator(24)] 
    )
    batch_percentage = models.DecimalField(
        max_digits=5,      
        decimal_places=2,    
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_batches', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_batches', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.batch_id

    @property
    def get_slottime(self):
        if self.start_time and self.end_time:
            return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
        return "Not Set"

    @classmethod
    def generate_batch_id(cls, category, course):
        """Generate a unique batch ID following the format <CategoryInitial><CourseCode><AlphaSeries2>"""
        with transaction.atomic():
            # Lock the table to prevent race conditions
            # Get the category initial
            category_initial = category.name[0].upper()
            
            # Get the course code (assuming it's stored in the course model)
            course_code = course.code[-2:].upper() if course.code else 'XX'
            
            # Find the last batch with this category and course combination
            last_batch = cls.objects.filter(
                course__category=category,
                course=course
            ).select_for_update().order_by('batch_id').last()
            
            if last_batch and last_batch.batch_id:
                # Extract the alpha series from the last batch ID
                try:
                    alpha_series = last_batch.batch_id[-2:]
                    # Convert alpha series to next in sequence (AA -> AB, AZ -> BA, etc.)
                    if alpha_series[1] == 'Z':
                        next_series = alpha_series[0] + 'A' if alpha_series[0] != 'Z' else 'AA'
                    else:
                        next_series = alpha_series[0] + chr(ord(alpha_series[1]) + 1)
                except (IndexError, ValueError):
                    next_series = 'AA'
            else:
                next_series = 'AA'
            
            # Construct the new batch ID
            return f"{category_initial}{course_code}{next_series}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Store user for signal handlers
        user = kwargs.pop('user', None)
        if user:
            self._user = user
            
        if not self.batch_id and self.course and self.course.category:
            self.batch_id = self.generate_batch_id(self.course.category, self.course)
        
        # Save the batch
        super().save(*args, **kwargs)

        if is_new:
            students = self.students.all()
            for student in students:
                batch_student, created = BatchStudent.objects.get_or_create(
                    batch=self,
                    student=student,
                    defaults={
                        'is_active': True,
                        'activated_at': timezone.now()
                    }
                )
                if created:
                    BatchTransaction.log_transaction(
                        batch=self,
                        transaction_type='STUDENT_ADDED',
                        user=user,
                        details={
                            'student_id': student.id,
                            'student_name': str(student),
                            'activated_at': str(batch_student.activated_at)
                        },
                        affected_students=[student]
                    )
        
        # Log the transaction if user is provided
        if user:
            transaction_type = 'BATCH_CREATED' if is_new else 'BATCH_UPDATED'
            BatchTransaction.log_transaction(
                batch=self,
                transaction_type=transaction_type,
                user=user,
                details={
                    'batch_id': self.batch_id,
                    'course': str(self.course) if self.course else None,
                    'trainer': str(self.trainer) if self.trainer else None,
                    'start_date': str(self.start_date),
                    'end_date': str(self.end_date),
                    'batch_type': self.get_batch_type_display(),
                    'batch_status': self.get_batch_status_display(),
                }
            )


class BatchStudent(models.Model):
    """Through model for tracking student batch history"""
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(default=timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Batch Student'
        verbose_name_plural = 'Batch Students'
    
    def __str__(self):
        return f"{self.student} - {self.batch} - {'Active' if self.is_active else 'Inactive'}"
    
    def save(self, *args, **kwargs):
        # Store user for signal handlers
        user = kwargs.pop('user', None)
        if user:
            self._user = user
        if not self.pk:  # only for new objects
            BatchStudent.objects.filter(
                student=self.student,
                batch=self.batch,
                is_active=True
            ).update(is_active=False, deactivated_at=timezone.now())
        # Call the original save method
        super().save(*args, **kwargs)
    
    def deactivate(self, user=None):
        """Deactivate a student from a batch"""
        if self.is_active:
            self.is_active = False
            self.deactivated_at = timezone.now()
            self.save(user=user)
            
            # Log the student removal transaction
            if user:
                BatchTransaction.log_transaction(
                    batch=self.batch,
                    transaction_type='STUDENT_REMOVED',
                    user=user,
                    details={
                        'student_id': self.student.id,
                        'student_name': str(self.student),
                        'deactivated_at': str(self.deactivated_at)
                    },
                    affected_students=[self.student]
                )
    
    def activate(self, user=None):
        """Activate a student in a batch"""
        if not self.is_active:
            self.is_active = True
            self.activated_at = timezone.now()
            self.deactivated_at = None
            self.save(user=user)
            
            # Log the student addition transaction
            if user:
                BatchTransaction.log_transaction(
                    batch=self.batch,
                    transaction_type='STUDENT_ADDED',
                    user=user,
                    details={
                        'student_id': self.student.id,
                        'student_name': str(self.student),
                        'activated_at': str(self.activated_at)
                    },
                    affected_students=[self.student]
                )

    @classmethod
    def get_student_batch_history(cls, student):
        """
        Retrieves the batch history for a specific student.
        """
        history = {
            'student_name': f"{student.first_name} {student.last_name or ''}".strip(),
            'current_batch': None,
            'batch_history': []
        }

        batch_students = cls.objects.filter(student=student).select_related('batch__course', 'batch__trainer').order_by('activated_at')

        for bs in batch_students:
            batch_info = {
                'pk': bs.batch.id,
                'batch_id': bs.batch.batch_id,
                'course': str(bs.batch.course) if bs.batch.course else 'N/A',
                'trainer': str(bs.batch.trainer) if bs.batch.trainer else 'N/A',
                'slot_time': bs.batch.get_slottime,
                'activated_at': bs.activated_at,
                'deactivated_at': bs.deactivated_at,
                'status': 'Active' if bs.is_active else 'Inactive'
            }
            if bs.is_active:
                history['current_batch'] = batch_info
            else:
                history['batch_history'].append(batch_info)
        
        # Also, fetch the transaction history for the student
        transactions = BatchTransaction.objects.filter(affected_students=student).select_related('batch', 'user').order_by('-timestamp')
        history['transactions'] = transactions
        
        return history


class BatchTransaction(models.Model):
    """Model for logging all batch-related events"""
    TRANSACTION_TYPES = [
        ('BATCH_CREATED', 'Batch Created'),
        ('BATCH_UPDATED', 'Batch Updated'),
        ('STUDENT_ADDED', 'Student Added'),
        ('STUDENT_REMOVED', 'Student Removed'),
        ('TRANSFER_OUT', 'Transfer Out'),
        ('TRANSFER_IN', 'Transfer In'),
        ('TRAINER_HANDOVER', 'Trainer Handover'),
    ]
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='batch_transactions')
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.JSONField(blank=True, null=True, help_text='Additional details about the transaction')
    affected_students = models.ManyToManyField(Student, blank=True, related_name='batch_transactions')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Batch Transaction'
        verbose_name_plural = 'Batch Transactions'
        indexes = [
            models.Index(fields=['batch', 'transaction_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.batch} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_transaction(cls, batch, transaction_type, user, details=None, affected_students=None):
        """Create a transaction log entry"""
        transaction = cls.objects.create(
            batch=batch,
            transaction_type=transaction_type,
            user=user,
            details=details
        )
        
        if affected_students:
            transaction.affected_students.set(affected_students)
        
        return transaction


class TrainerHandover(models.Model):
    """Model for tracking trainer handovers in batches"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='trainer_handovers')
    from_trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='handovers_from')
    to_trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='handovers_to')
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_handovers')
    requested_at = models.DateTimeField(default=timezone.now)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_handovers')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True, null=True)
    handover_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Trainer Handover'
        verbose_name_plural = 'Trainer Handovers'
    
    def __str__(self):
        return f"Handover from {self.from_trainer} to {self.to_trainer} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # If the object is being created
            self.expires_at = timezone.now() + timezone.timedelta(minutes=2)
        super().save(*args, **kwargs)

    @transaction.atomic
    def approve(self, approved_by, remarks=None):
        """Approve the trainer handover"""
        if self.status != 'PENDING':
            raise ValueError("Only pending handover requests can be approved.")
        
        if self.expires_at < timezone.now():
            self.reject(approved_by, remarks="Request expired and was automatically rejected.")
            raise ValueError("This handover request has expired and has been rejected.")

        # Update handover record
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        
        if remarks:
            self.remarks = remarks
        
        self.save()
        
        # Update the batch's trainer
        old_trainer = self.batch.trainer
        self.batch.trainer = self.to_trainer
        self.batch.save()
        
        # Log the trainer handover transaction
        BatchTransaction.log_transaction(
            batch=self.batch,
            transaction_type='TRAINER_HANDOVER',
            user=approved_by,
            details={
                'handover_id': self.id,
                'from_trainer_id': self.from_trainer.id,
                'from_trainer_name': str(self.from_trainer),
                'to_trainer_id': self.to_trainer.id,
                'to_trainer_name': str(self.to_trainer),
                'remarks': remarks
            }
        )
        
        return self.batch
    
    def reject(self, rejected_by, remarks=None):
        """Reject the trainer handover"""
        if self.status != 'PENDING':
            raise ValueError("Only pending handover requests can be rejected.")
        
        if self.expires_at < timezone.now():
            self.status = 'EXPIRED'
            self.save()
            raise ValueError("This handover request has expired and cannot be rejected.")

        self.status = 'REJECTED'
        self.approved_by = rejected_by  # Using the same field for rejection tracking
        self.approved_at = timezone.now()
        
        if remarks:
            self.remarks = remarks
        
        self.save()

    @classmethod
    def expire_pending_requests(cls):
        """Expires pending requests that have passed their expiration time."""
        cls.objects.filter(
            status='PENDING',
            expires_at__lte=timezone.now()
        ).update(status='EXPIRED')


class TransferRequest(models.Model):
    """Model for student transfer requests between batches"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    from_batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='transfer_requests_from')
    to_batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='transfer_requests_to')
    students = models.ManyToManyField(Student, related_name='transfer_requests')
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_transfers')
    requested_at = models.DateTimeField(default=timezone.now)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transfers')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Transfer Request'
        verbose_name_plural = 'Transfer Requests'
    
    def __str__(self):
        return f"Transfer from {self.from_batch} to {self.to_batch} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # If the object is being created
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    @classmethod
    def expire_pending_requests(cls):
        """Expires pending requests that have passed their expiration time."""
        cls.objects.filter(
            status='PENDING',
            expires_at__lte=timezone.now()
        ).update(status='EXPIRED')

    @transaction.atomic
    def approve(self, approved_by, approved_students=None, remarks=None):
        """Approve the transfer request for all or specific students"""
        if self.status != 'PENDING':
            raise ValueError("Only pending transfer requests can be approved.")
        
        if self.expires_at < timezone.now():
            self.reject(approved_by, remarks="Request expired and was automatically rejected.")
            raise ValueError("This transfer request has expired and has been rejected.")

        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        
        if remarks:
            self.remarks = remarks
        
        self.save()
        
        # Get the students to transfer
        students_to_transfer = approved_students if approved_students else self.students.all()
        
        # Process each student transfer
        for student in students_to_transfer:
            # Deactivate in the source batch
            try:
                batch_student = BatchStudent.objects.get(batch=self.from_batch, student=student)
                batch_student.deactivate(user=approved_by)
                
                # Log the transfer out transaction
                BatchTransaction.log_transaction(
                    batch=self.from_batch,
                    transaction_type='TRANSFER_OUT',
                    user=approved_by,
                    details={
                        'transfer_request_id': self.id,
                        'to_batch_id': self.to_batch.id,
                        'to_batch': self.to_batch.batch_id,
                        'remarks': remarks
                    },
                    affected_students=[student]
                )
            except BatchStudent.DoesNotExist:
                pass
            
            # Deactivate any existing entries for the student in the destination batch.
            BatchStudent.objects.filter(batch=self.to_batch, student=student, is_active=True).update(
                is_active=False,
                deactivated_at=timezone.now()
            )

            # Create a new active entry for the student in the destination batch.
            batch_student = BatchStudent.objects.create(
                batch=self.to_batch,
                student=student,
                is_active=True,
                activated_at=timezone.now()
            )
            
            # Log the transfer in transaction
            BatchTransaction.log_transaction(
                batch=self.to_batch,
                transaction_type='TRANSFER_IN',
                user=approved_by,
                details={
                    'transfer_request_id': self.id,
                    'from_batch_id': self.from_batch.id,
                    'from_batch': self.from_batch.batch_id,
                    'remarks': remarks
                },
                affected_students=[student]
            )
        
        return students_to_transfer
    
    def reject(self, rejected_by, remarks=None):
        """Reject the transfer request"""
        if self.status != 'PENDING':
            raise ValueError("Only pending transfer requests can be rejected.")
        
        if self.expires_at < timezone.now():
            self.status = 'EXPIRED'
            self.save()
            raise ValueError("This transfer request has expired and cannot be rejected.")

        self.status = 'REJECTED'
        self.approved_by = rejected_by  # Using the same field for rejection tracking
        self.approved_at = timezone.now()
        
        if remarks:
            self.remarks = remarks
        
        self.save()
