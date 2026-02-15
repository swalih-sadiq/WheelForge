from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, otp, purpose):
    subject = "WheelForge OTP Verification"

    if purpose == "signup":
        message = f"""Welcome to WheelForge!
        
        To complete your registration, please use the One-Time Password (OTP): {otp}
        This OTP is valid for 5 minutes.
       
         — The WheelForge Team"""
    
    elif purpose == "forgot_password":
        message = f"""We received a request to reset your WheelForge password.
        Use the OTP  to proceed: {otp}
        This OTP is valid for 5 minutes.
        
        — WheelForge Support"""
        
    else:
        message = f"Your OTP is: {otp}"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
