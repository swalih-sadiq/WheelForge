import time

from django.shortcuts import render, redirect 
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings

from django.contrib.auth import get_user_model

from .utils import generate_otp, clear_email_change_session 

User = get_user_model()

@never_cache
@login_required
def request_email_change_view(request):
    if request.user.auth_provider != 'email':
        messages.error(
            request,
            'Email change is not allowed for social login accounts.'
        )
        return redirect('profile')

    if request.method == "POST":
        new_email = request.POST.get("email").strip().lower()

        if not new_email:
            messages.error(request, "Email is required.")
            return redirect("request-email-change")

        if new_email == request.user.email:
            messages.error(request, "New email must be different.")
            return redirect("request-email-change")
        
        if User.objects.filter(email=new_email).exists():
            messages.error(
                request,
                "This email is already in use."
            )
            return redirect("request-email-change")

        # ---------- RATE LIMIT (max 3) ----------
        attempts = request.session.get("email_change_attempts", 0)
        if attempts >= 3:
            messages.error(
                request,
                "Too many OTP requests. Try again later."
            )
            return redirect("request-email-change")

        # ---------- CREATE OTP ----------
        otp = generate_otp()

        request.session["email_change_otp"] = otp
        request.session["email_change_new_email"] = new_email
        request.session["email_change_time"] = int(time.time())
        request.session["email_change_attempts"] = attempts + 1

        # ---------- SEND OTP ----------
        send_mail(
            subject="WheelForge - Email Change OTP",
            message=f"Your OTP is {otp}. Valid for 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
            fail_silently=False,
        )

        messages.success(
            request,
            "OTP sent to your new email address."
        )
        return redirect("verify-email-change-otp")

    return render(request, "accounts/request_email_change.html")


@never_cache
@login_required
def verify_email_change_otp_view(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        session_otp = request.session.get("email_change_otp")
        new_email = request.session.get("email_change_new_email")
        otp_time = request.session.get("email_change_time")

        if not session_otp or not new_email or not otp_time:
            messages.error(request, "Session expired. Try again.")
            return redirect("request-email-change")

        # ---------- OTP EXPIRY ----------
        if int(time.time()) - otp_time > 300:
            messages.error(request, "OTP expired.")
            clear_email_change_session(request)
            return redirect("request-email-change")

        if entered_otp != session_otp:
            messages.error(request, "Invalid OTP.")
            return redirect("verify-email-change-otp")
        
        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            messages.error(
                request,
                "This email is already in use."
            )
            clear_email_change_session(request)
            return redirect("request-email-change")

        # ---------- UPDATE EMAIL ----------
        old_email = request.user.email
        request.user.email = new_email
        request.user.save()

        send_mail(
            subject="WheelForge - Email Changed",
            message="Your email address has been updated successfully.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[old_email],
            fail_silently=True,
        )

        clear_email_change_session(request)

        messages.success(
            request,
            "Email updated successfully."
        )
        return redirect("profile", uuid=request.user.uuid)

    return render(request, "accounts/verify_email_change_otp.html")
