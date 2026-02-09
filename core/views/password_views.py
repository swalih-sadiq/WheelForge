from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash 
from django.shortcuts import render, redirect , get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import OTPVerification
from .utils import generate_otp

User = get_user_model()

@login_required(login_url='login')
def forgot_password_view(request):
    if request.method == "POST":
        user = request.user
        email = user.email

        if not email:
            messages.error(request, "Email is required.")
            return redirect("forgot_password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.success(
                request,
                "If this email exists, an OTP has been sent."
            )
            return redirect("login")

        if user.is_blocked:
            messages.error(
                request,
                "Your account has been blocked."
            )
            return redirect("login")

        recent_otp_exists = OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password",
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).exists()

        if recent_otp_exists:
            messages.warning(
                request,
                "Please wait before requesting another OTP."
            )
            return redirect("forgot_password")

        OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password",
            is_verified=False
        ).update(is_verified=True)

        otp = generate_otp()

        OTPVerification.objects.create(
            user=user,
            otp=otp,
            purpose="forgot_password",
            expires_at=OTPVerification.get_expiry_time()
        )


        request.session["otp_user_id"] = user.id
        request.session["otp_purpose"] = "forgot_password"

        messages.success(
            request,
            "OTP sent to your email."
        )
        return redirect("verify_forgot_otp")

    return render(request, "forgot_password.html")

@login_required(login_url='login')
def verify_forgot_otp_view(request):

    if request.session.get("otp_purpose") != "forgot_password":
        messages.error(request, "Invalid OTP session.")
        return redirect("forgot_password")

    if request.session.get("otp_user_id") != request.user.id:
        messages.error(request, "Unauthorized OTP access.")
        return redirect("forgot_password")
        
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(
            request,
            "Session expired. Please try again."
        )
        return redirect("forgot_password")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        otp_input = request.POST.get("otp")

        try:
            otp_obj = OTPVerification.objects.filter(
                user=user,
                purpose="forgot_password",
                is_verified=False
            ).latest("created_at")
        except OTPVerification.DoesNotExist:
            messages.error(request, "No OTP found.")
            return redirect("forgot_password")

        if otp_obj.is_expired():
            messages.error(request, "OTP expired.")
            return redirect("forgot_password")

        if otp_obj.otp != otp_input:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_forgot_otp")

        otp_obj.is_verified = True
        otp_obj.save()

        messages.success(
            request,
            "OTP verified. Set a new password."
        )
        return redirect("reset_password")

    return render(request, "verify_forgot_otp.html")

def reset_password_view(request):
    user_id = request.session.get("otp_user_id")
    purpose = request.session.get("otp_purpose")

    if not user_id or purpose != "forgot_password":
        messages.error(
            request,
            "Session expired. Please try again."
        )
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not password or not confirm_password:
            messages.error(
                request,
                "All fields are required."
            )
            return redirect("reset_password")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return redirect("reset_password")

        user.set_password(password)
        user.save()

        OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password"
        ).delete()

        request.session.pop("otp_user_id", None)
        request.session.pop("otp_purpose", None)

        messages.success(
            request,
            "Password reset successful. Please log in."
        )
        return redirect("login")

    return render(request, "reset_password.html")


@login_required
def change_password_view(request, uuid):
    print("METHOD:", request.method)
    print("POST DATA:", request.POST)
    user = get_object_or_404(User, uuid=uuid)

    # users can change ONLY their own password
    if request.user != user:
        messages.error(request, "Unauthorized action.")
        return redirect("profile", request.user.uuid)

    if request.method == "POST":
        form = PasswordChangeForm(user=user, data=request.POST)

        if form.is_valid():
            updated_user = form.save()

            # KEEP SESSION ALIVE (CRITICAL)
            update_session_auth_hash(request, updated_user)

            messages.success(request, "Password changed successfully.")
            return redirect("profile", user.uuid)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=user)

    return render(
        request,
        "change_password.html",
        {
            "form": form,
            "user_obj": user
        }
    )