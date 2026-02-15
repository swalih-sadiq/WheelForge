from django.shortcuts import render, redirect 
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from django.contrib.auth import get_user_model

from accounts.models import OTPVerification
from accounts.utils.otp import generate_otp
from accounts.utils.clear_email_session import clear_email_change_session
from core.utils.validators import validate_email_change_data

User = get_user_model()

@never_cache
@login_required
def request_email_change_view(request):
    if request.user.auth_provider != 'email':
        messages.error(request,'Email change is not allowed for social login accounts.')
        return redirect('profile', uuid=request.user.uuid)

    new_email = request.session.get("email_change_new_email")

    if not new_email:
        messages.error(request, "Invalid email change request.")
        return redirect("profile", uuid=request.user.uuid)

    #   VALIDATION 
    errors = validate_email_change_data(
        {'email': new_email},
            current_email=request.user.email
    )
    if errors:
        for error in errors.values():
            messages.error(request, error)
        return redirect('edit_profile', uuid=request.user.uuid)
    
    if User.objects.filter(email=new_email).exists():
        messages.error(request, "This email is already in use.")
        return redirect("edit_profile", uuid=request.user.uuid)

    # ---------- RATE LIMIT ----------
    attempts = request.session.get("email_change_attempts", 0)
    if attempts >= 3:
        messages.error(request,"Too many OTP requests. Try again later.")
        return redirect("profile", uuid=request.user.uuid)
    
    # Invalidate old OTPs
    OTPVerification.objects.filter(
        user=request.user,
        purpose="email_change",
        is_verified=False
    ).update(is_verified=True)

    otp = generate_otp()

    otp_obj = OTPVerification.objects.create(
        user=request.user,
        otp=otp,
        purpose="email_change",
        expires_at=timezone.now() + timedelta(minutes=5)
    )

        #  SESSION POINTER
    request.session["email_change_otp_id"] = otp_obj.id
    # request.session["email_change_new_email"] = new_email
    request.session["email_change_attempts"] = attempts + 1

    #  SEND EMAIL
    send_mail(
        subject="WheelForge - Email Change OTP",
        message=f"""To confirm this change, use the OTP is {otp}. 
        Valid for 5 minutes.
        
        
        — The WheelForge Team""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email],
        fail_silently=False,
    )

    messages.success(request,"OTP sent to your new email address.")
    return redirect("verify-email-change-otp")

    # return render(request, "accounts/request_email_change.html")



@never_cache
@login_required
def verify_email_change_otp_view(request):

    otp_id = request.session.get("email_change_otp_id")
    new_email = request.session.get("email_change_new_email")

    if not otp_id or not new_email:
        messages.error(request, "Session expired. Try again.")
        return redirect("request-email-change")

    try:
        otp_record = OTPVerification.objects.get(
            id=otp_id,
            purpose="email_change",
            user=request.user,
            is_verified=False
        )
    except OTPVerification.DoesNotExist:
        messages.error(request, "Invalid or expired OTP.")
        return redirect("request-email-change")

    # ---------- EXPIRY CHECK ----------
    if timezone.now() > otp_record.expires_at:
        messages.error(request, "OTP expired.")
        otp_record.delete()
        return redirect("request-email-change")
    
    #  CALCULATE REMAINING TIME 
    remaining_seconds = max(
        int((otp_record.expires_at - timezone.now()).total_seconds()),
        0
    )

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        if entered_otp != otp_record.otp:
            messages.error(request, "Invalid OTP.")
            return redirect("verify-email-change-otp")

        #  UPDATE EMAIL
        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            messages.error(request, "This email is already in use.")
            return redirect("request-email-change")

        old_email = request.user.email
        request.user.email = new_email
        request.user.save()

        otp_record.is_used = True
        otp_record.save()

        clear_email_change_session(request)

        send_mail(
            subject="WheelForge - Your Email Has Been Updated",
            message="""This is a confirmation that your WheelForge account email has been successfully updated.

            
            — The WheelForge Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[old_email],
            fail_silently=True,
        )

        messages.success(request, "Email updated successfully.")
        return redirect("profile", uuid=request.user.uuid)

    return render(request, "accounts/verify_email_change_otp.html", {"otp_remaining_seconds": remaining_seconds})



@never_cache
@login_required
def resend_email_change_otp_view(request):
    new_email = request.session.get("email_change_new_email")
    attempts = request.session.get("email_change_attempts", 0)
    otp_id = request.session.get("email_change_otp_id")

    #  SESSION VALIDATION 
    if not new_email:
        messages.error(request, "Session expired. Try again.")
        return redirect("request-email-change")

    #  RATE LIMIT 
    if attempts >= 3:
        messages.error(request,"Too many OTP requests. Please wait before trying again.")
        return redirect("verify-email-change-otp")

    if otp_id:
        OTPVerification.objects.filter(
            id=otp_id,
            purpose="email_change",
            user=request.user,
            is_used=False
        ).update(is_used=True)

    otp = generate_otp()

    otp_record = OTPVerification.objects.create(
        user=request.user,
        otp=otp,
        purpose="email_change",
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    #  STORE ONLY REFERENCE IN SESSION 
    request.session["email_change_otp_id"] = otp_record.id
    request.session["email_change_attempts"] = attempts + 1

    send_mail(
        subject="WheelForge - Email Change OTP",
        message=f""" You requested to change the email address linked to your WheelForge account.
        To confirm this change, use the OTP: {otp}.
        This OTP will expire in 5 minutes.
        
        — The WheelForge Team""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email],
        fail_silently=False,
    )

    messages.success(request, "OTP resent successfully.")
    return redirect("verify-email-change-otp")

