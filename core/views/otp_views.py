from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from .utils import generate_otp

from accounts.models import OTPVerification

User = get_user_model()

def verify_otp_view(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(
            request,
            "Session expired. Please sign up again."
        )
        return redirect("signup")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        otp_input = request.POST.get("otp")

        try:
            otp_obj = OTPVerification.objects.filter(
                user=user,
                purpose="signup",
                is_verified=False
            ).latest("created_at")
        except OTPVerification.DoesNotExist:
            messages.error(request, "No OTP found.")
            return redirect("signup")

        if otp_obj.is_expired():
            messages.error(request, "OTP expired.")
            return redirect("signup")

        if otp_obj.otp != otp_input:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_otp")

        otp_obj.is_verified = True
        otp_obj.save()

        user.is_active = True
        user.save()

        del request.session["otp_user_id"]

        messages.success(
            request,
            "Account verified. You can now log in."
        )
        return redirect("login")

    return render(request, "verify_otp.html")


def resend_otp_view(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(
            request,
            "Session expired. Please login again."
        )
        return redirect("login")

    user = User.objects.get(id=user_id)

    recent_otp_exists = OTPVerification.objects.filter(
        user=user,
        purpose="signup",
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).exists()

    if recent_otp_exists:
        messages.warning(
            request,
            "Please wait before requesting a new OTP."
        )
        return redirect("verify_otp")

    OTPVerification.objects.filter(
        user=user,
        purpose="signup",
        is_verified=False
    ).update(is_verified=True)

    otp = OTPVerification.objects.create(
        user=user,
        otp=generate_otp(),
        purpose="signup",
        expires_at=OTPVerification.get_expiry_time()
    )

    print(f"RESEND OTP for {user.email}: {otp.otp}")
    messages.success(
        request,
        "OTP resent successfully."
    )
    return redirect("verify_otp")
