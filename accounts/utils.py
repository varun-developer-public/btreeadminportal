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