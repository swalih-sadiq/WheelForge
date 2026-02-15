from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash 
from django.shortcuts import render, redirect , get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import OTPVerification
from core.utils.otp import generate_otp
from core.utils.email import send_otp_email
from core.utils.validators import validate_forgot_password_data
from core.utils.validators import validate_reset_password_data
from core.decorators import user_required

User = get_user_model()

@never_cache
def forgot_password_view(request):
    if request.method == "POST":

        # Clear previous forgot sessions
        for key in list(request.session.keys()):
            if key.startswith('forgot_'):
                request.session.pop(key, None)

        errors = validate_forgot_password_data(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request, error)
            return redirect("forgot_password")

        email = request.POST.get("email").strip().lower()

        try:
            user = User.objects.get(email=email)

            if user.is_blocked:
                messages.error(request, "Your account has been blocked.")
                return redirect("login")

            otp = generate_otp()

            #  CREATE OTP IN DB
            otp_record = OTPVerification.objects.create(
                email=email,
                otp=otp,
                purpose="forgot_password",
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )

            #  STORE ONLY ID IN SESSION
            request.session['forgot_otp_id'] = otp_record.id
            request.session['forgot_user_id'] = user.id
            request.session['forgot_verified'] = False

            send_otp_email(email, otp, 'forgot_password')

        except User.DoesNotExist:
            pass

        messages.success(request, "If this email exists, an OTP has been sent.")
        return redirect("verify_forgot_otp")

    return render(request, "forgot_password.html")


@never_cache
def verify_forgot_otp_view(request):

    otp_id = request.session.get('forgot_otp_id')
    user_id = request.session.get('forgot_user_id')

    if not otp_id or not user_id:
        messages.error(request, "Session expired. Please try again.")
        return redirect("forgot_password")

    try:
        otp_record = OTPVerification.objects.get(
            id=otp_id,
            purpose="forgot_password"
        )
    except OTPVerification.DoesNotExist:
        messages.error(request, "Invalid session.")
        return redirect("forgot_password")

    # Expiry check
    if timezone.now() > otp_record.expires_at:
        otp_record.delete()
        messages.error(request, "OTP expired. Please try again.")
        return redirect("forgot_password")
    
    # CALCULATE REMAINING TIME
    remaining_seconds = max(
        int((otp_record.expires_at - timezone.now()).total_seconds()),
        0
    )

    if otp_record.is_used:
        messages.error(request, "OTP already used.")
        return redirect("forgot_password")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        if entered_otp != otp_record.otp:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_forgot_otp")

        #  Mark as used
        otp_record.is_used = True
        otp_record.save()

        request.session['forgot_verified'] = True
        messages.success(request, "OTP verified. You can now reset your password.")
        return redirect("reset_password")

    return render(request, "verify_forgot_otp.html", {"otp_remaining_seconds": remaining_seconds})


@never_cache
def reset_password_view(request):

    user_id = request.session.get("forgot_user_id")
    verified = request.session.get("forgot_verified")
    otp_id = request.session.get("forgot_otp_id")

    #  SECURITY CHECK (Hybrid enforcement)
    if not user_id or not verified or not otp_id:
        messages.error(request, "Unauthorized access.")
        return redirect("forgot_password")

    try:
        otp_record = OTPVerification.objects.get(
            id=otp_id,
            purpose="forgot_password",
            is_used=True
        )
    except OTPVerification.DoesNotExist:
        messages.error(request, "Invalid or expired session.")
        return redirect("forgot_password")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("forgot_password")

    if request.method == "POST":

        errors = validate_reset_password_data(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request, error)
            return redirect("reset_password")

        password = request.POST.get("password")

        user.set_password(password)
        user.save()

        #  Cleanup session
        for key in list(request.session.keys()):
            if key.startswith("forgot_"):
                request.session.pop(key, None)

        messages.success(request, "Password reset successful. Please log in.")
        return redirect("login")

    return render(request, "reset_password.html")


@never_cache
@user_required
def change_password_view(request, uuid):

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

    return render(request,"change_password.html",{"form": form, "user_obj": user})