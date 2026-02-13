from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.cache import never_cache 
from django.core.mail import send_mail
from django.conf import settings
from core.utils.otp import generate_otp
from core.utils.email import send_otp_email

from accounts.models import OTPVerification

User = get_user_model()

@never_cache
def verify_otp_view(request):
    email = request.session.get('signup_email')
    otp_session = request.session.get('signup_otp')
    created_at = request.session.get('signup_otp_created_at')

    if not email or not otp_session or not created_at:
        messages.error(request, 'Session expired. Please sign up again.')
        return redirect('signup')
    
    if timezone.now() > timezone.datetime.fromisoformat(created_at) + timezone.timedelta(minutes=5):
        for key in list(request.session.keys()):
            if key.startswith('signup_'):
                request.session.pop(key, None)
        messages.error(request, 'OTP expired. Please sign up again.')
        return redirect('signup')
    
    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()

        if otp_input != otp_session:
            messages.error(request, 'Invalid OTP.')
            return redirect('verify_otp')
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=request.session['signup_password'],
            is_active=True
        )

        OTPVerification.objects.filter(
            purpose='signup',
            otp=otp_session,
            is_verified=False
        ).update(is_verified=True)

        for key in list(request.session.keys()):
            if key.startswith('signup_'):
                request.session.pop(key, None)

        messages.success(request,"Account verified. You can now log in.")
        return redirect("login")

    return render(request, "verify_otp.html")

@never_cache
def resend_otp_view(request):
    email = request.session.get('signup_email')
    created_at = request.session.get('signup_otp_created_at')

    if not email or not created_at:
        messages.error(request, "Session expired. Please sign up again")
        return redirect ('signup')
    
    created_at = timezone.datetime.fromisoformat(created_at)

    if timezone.now() < created_at + timezone.timedelta(seconds=60):
        messages.warning(request, 'please wait before requesting a new OTP.')
        return redirect('verify_otp')
    
    new_otp = generate_otp()

    request.session['signup_otp'] = new_otp
    request.session['signup_otp_created_at'] = timezone.now().isoformat()

    # otp via session
    # OTPVerification.objects.filter(
    #     purpose='signup',
    #     is_verified=False
    # ).update(is_verified=True)

    # OTPVerification.objects.create(
    #     otp=new_otp,
    #     purpose='signup',
    #     expires_at=OTPVerification.get_expiry_time()
    # )

    send_otp_email(email, new_otp, 'signup')
    messages.success(request,"A new OTP has been sent to your email.")
    return redirect("verify_otp")
