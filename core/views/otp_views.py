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

def verify_otp_view(request):

    user_id = request.session.get("otp_user_id")
    purpose = request.session.get("otp_purpose")

    if not user_id or purpose != 'signup':
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("signup")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid session.")
        return redirect("signup")
    
    try:
        otp_obj = OTPVerification.objects.filter(
            user=user,
            purpose='signup',
            is_verified=False
        ).latest("created_at")
    except OTPVerification.DoesNotExist:
        messages.error(request, "No OTP found.")
        return redirect("signup")
    
    remaining_seconds = 0

    if otp_obj.expires_at and otp_obj.expires_at > timezone.now():
        remaining_seconds = int(
            (otp_obj.expires_at - timezone.now()).total_seconds()
        )

    if request.method == "POST":
        otp_input = request.POST.get("otp", "").strip()

        

        #  Expiry check
        if otp_obj.is_expired():
            messages.error(request, "OTP expired.")
            return redirect("signup")

        #  OTP match
        if otp_obj.otp != otp_input:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_otp")

        #  Mark verified
        otp_obj.is_verified = True
        otp_obj.save()

        #  Activate user
        user.is_active = True
        user.save()

        #  Clear session
        request.session.pop('otp_user_id', None)
        request.session.pop('otp_purpose', None)

        messages.success(request, "Account verified. You can now log in.")
        return redirect("login")

    return render(request, "verify_otp.html", {"otp_remaining_seconds": remaining_seconds})

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
