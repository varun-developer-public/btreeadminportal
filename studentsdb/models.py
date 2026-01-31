from django.db import models
from django.utils import timezone
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining
from .field_choices import DEGREE_CHOICES, BRANCH_CHOICES
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from settingsdb.signals import get_current_user
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
 
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
        ('P', 'Placed'),
        ('IA', 'In Active')
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_students')

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

class StudentConversation(models.Model):
    student = models.OneToOneField('Student', on_delete=models.CASCADE, related_name='conversation')
    is_priority = models.BooleanField(default=False)
    priority_level = models.IntegerField(default=0)  # 1-5, 0 for none
    last_message = models.TextField(blank=True, default='')
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='last_message_conversations')
    unread_count = models.PositiveIntegerField(default=0)
    # New fields to track priority derived ONLY from the latest message
    last_message_priority = models.BooleanField(default=False)
    last_message_priority_level = models.IntegerField(default=0)
    last_message_hashtag = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.student.student_id}"

class ConversationMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ("text", "Text"),
        ("file", "File"),
    )
    conversation = models.ForeignKey(StudentConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    sender_role = models.CharField(max_length=50, blank=True)
    hashtag = models.CharField(max_length=100, blank=True, default='')
    priority = models.CharField(max_length=10, blank=True, choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text")
    message = models.TextField(blank=True)
    file = models.FileField(upload_to="student_conversation/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_mime = models.CharField(max_length=100, blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class MessageReadStatus(models.Model):
    message = models.ForeignKey(ConversationMessage, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')


def apply_feedback_from_message(message_instance, user=None):
    try:
        from paymentdb.models import Payment, PendingPaymentRecord
        conv = message_instance.conversation
        student = conv.student
        payment = Payment.objects.filter(student=student).first()
        if not payment:
            return None
        created_record = False
        try:
            record = payment.pending_record
        except PendingPaymentRecord.DoesNotExist:
            record = PendingPaymentRecord(
                payment=payment,
                student=student,
                student_code=student.student_id,
                student_name=f"{student.first_name} {student.last_name or ''}",
                course_status=getattr(student, 'course_status', '')
            )
            record.refresh_from_sources()
            created_record = True
        msg_text = (message_instance.message or '').strip()
        if msg_text:
            record.feedback = msg_text
        if user and getattr(user, 'is_authenticated', False):
            record.edited_by = user
            if record.created_by is None:
                record.created_by = user
        elif message_instance.sender:
            record.edited_by = message_instance.sender
        if created_record:
            record.save()
        else:
            if msg_text:
                record.save(update_fields=['feedback', 'edited_by', 'updated_at'])
            else:
                record.save(update_fields=['edited_by', 'updated_at'])
        updated_by_name = (
            getattr(record.edited_by, 'name', None)
            or getattr(record.edited_by, 'email', None)
            or getattr(record.edited_by, 'username', None)
        )
        return {
            'feedback': record.feedback or '',
            'updated_by_name': updated_by_name or '',
            'updated_at': record.updated_at.isoformat(),
            'student_pk': student.id,
        }
    except Exception:
        return None

@receiver(post_save, sender=Student)
def create_student_conversation(sender, instance, created, **kwargs):
    if created:
        conv, _ = StudentConversation.objects.get_or_create(student=instance)

def send_payment_onboarding_message(sender, instance, created, **kwargs):
    if created:
        # instance is Payment
        student = instance.student
        conv, _ = StudentConversation.objects.get_or_create(student=student)
        
        try:
            user = get_current_user()
        except Exception:
            user = None
            
        if user and getattr(user, 'is_authenticated', False):
            course_name = "N/A"
            if student.course:
                course_name = student.course.course_name
            
            student_name = f"{student.first_name} {student.last_name or ''}".strip()
            emi_count = instance.emi_type if instance.emi_type != 'NONE' else '0'
            
            message_text = (
                f"I have onboarded the student {student_name} - {student.student_id} today for the course {course_name} "
                f"with {emi_count} EMI split. "
            )

            ConversationMessage.objects.create(
                conversation=conv,
                sender=user,
                sender_role=getattr(user, 'role', '') or '',
                message=message_text
            )

@receiver(post_save, sender=ConversationMessage)
def sync_pending_feedback_on_conversation(sender, instance, created, **kwargs):
    if not created:
        return
    apply_feedback_from_message(instance, user=instance.sender)

@receiver(post_save, sender=ConversationMessage)
def update_conversation_stats(sender, instance, created, **kwargs):
    if not created:
        return
    
    conv = instance.conversation
    conv.last_message = instance.message
    conv.last_message_at = instance.created_at
    conv.last_message_by = instance.sender
    
    # Increment unread count logic:
    # Any message that is NOT from an admin/staff/internal role should increment unread count.
    # We check both the user flags and the role string.
    is_internal_sender = False
    if instance.sender:
        # Check Django flags
        if instance.sender.is_staff or instance.sender.is_superuser:
            is_internal_sender = True
        # Check explicit role
        elif instance.sender_role and instance.sender_role.lower() in ['admin', 'staff', 'batch_coordination', 'consultant', 'trainer', 'placement']:
            is_internal_sender = True
            
    # If sender is None (Anonymous) or not internal, treat as student message
    if not is_internal_sender:
        conv.unread_count += 1
    
    # Update priority derived ONLY from this latest message
    # Reset first
    conv.last_message_priority = False
    conv.last_message_priority_level = 0
    conv.last_message_hashtag = instance.hashtag or ''
    
    if instance.priority:
        conv.last_message_priority = True
        if instance.priority == 'high':
            conv.last_message_priority_level = 3
        elif instance.priority == 'medium':
            conv.last_message_priority_level = 2
        elif instance.priority == 'low':
            conv.last_message_priority_level = 1
            
    # Also update the legacy/cumulative priority fields to match this latest message logic
    # The user requested that star/background come only based on the last message.
    # So we overwrite the cumulative fields with the latest message's state.
    conv.is_priority = conv.last_message_priority
    conv.priority_level = conv.last_message_priority_level
            
    conv.save()
    
    # Send WebSocket update
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "student_remarks",
        {
            "type": "broadcast",
            "payload": {
                "action": "remarks_list_update",
                "student_id": conv.student.id,
                "message": {
                    "message": conv.last_message,
                    "created_at": conv.last_message_at.isoformat() if conv.last_message_at else "",
                    "sender_id": instance.sender.id if instance.sender else None,
                    "priority": instance.priority,
                    "hashtag": instance.hashtag
                },
                "unread_count": conv.unread_count,
                "is_priority": conv.is_priority,
                "priority_level": conv.priority_level
            }
        }
    )
