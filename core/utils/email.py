from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, otp, purpose):
    subject = "WheelForge OTP Verification"

    if purpose == "signup":
        message = f"Your WheelForge signup OTP is: {otp}"
    elif purpose == "forgot_password":
        message = f"Your password reset OTP is: {otp}"
    else:
        message = f"Your OTP is: {otp}"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
