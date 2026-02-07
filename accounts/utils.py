from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import date

def send_otp_email(email, otp):
    subject = "Password Reset RequestOTP"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email]

    # Plain text fallback
    text_content = f"Your OTP for password reset is: {otp}"

    # HTML template
    html_content = f"""
    <div style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#ffffff; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1); padding:30px;">
            <h2 style="color:#333; text-align:center;">🔐 Password Reset Request</h2>
            <p style="font-size:16px; color:#555; text-align:center;">
                We received a request to reset your password. Please use the OTP below to proceed:
            </p>
            <div style="text-align:center; margin:30px 0;">
                <span style="font-size:28px; font-weight:bold; color:#2c3e50; letter-spacing:3px; display:inline-block; background:#f1f1f1; padding:10px 20px; border-radius:8px;">
                    {otp}
                </span>
            </div>
            <p style="font-size:14px; color:#777; text-align:center;">
                This OTP is valid for the next <b>3 minutes</b>. If you didn’t request this, you can safely ignore this email.
            </p>
            <hr style="margin:20px 0; border:none; border-top:1px solid #eee;">
            <p style="font-size:12px; color:#aaa; text-align:center;">
                © {date.today().year} BTree | This is an automated email, please do not reply.
            </p>
        </div>
    </div>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

from django.utils import timezone
from studentsdb.models import ConversationMessage

def get_unread_mentions(user):
    if not user.is_authenticated:
        return []
    
    # Messages where user is mentioned AND NOT read by user
    messages = ConversationMessage.objects.filter(
        mentions=user
    ).exclude(
        read_statuses__user=user
    ).select_related('sender', 'conversation__student').order_by('-created_at')
    
    notifs = []
    for msg in messages:
        student = msg.conversation.student
        student_name = f"{student.first_name} {student.last_name or ''}"
        sender_name = msg.sender.name if msg.sender else "Unknown"
        
        # Calculate time diff
        time_diff = timezone.now() - msg.created_at
        if time_diff.days > 0:
            time_str = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_str = f"{time_diff.seconds // 3600} hours ago"
        elif time_diff.seconds > 60:
            time_str = f"{time_diff.seconds // 60} minutes ago"
        else:
            time_str = "Just now"
        
        notifs.append({
            'id': f"mention_{msg.id}",
            'message_id': msg.id,
            'student_id': student.id,
            'student_name': student_name,
            'content': f"You were mentioned by {sender_name} in {student_name}'s chat",
            'time': time_str,
            'read': False
        })
    return notifs