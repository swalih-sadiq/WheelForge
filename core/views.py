import random
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required 
from django.utils import timezone


from accounts.models import OTPVerification

User = get_user_model()


def generate_otp():
    return str(random.randint(100000, 999999))


def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            is_active=False
        )

        otp = generate_otp()

        OTPVerification.objects.create(
            user=user,
            otp=otp,
            purpose="signup",
            expires_at=OTPVerification.get_expiry_time()
        )

        # TEMP: print OTP to console
        print(f"SIGNUP OTP for {email}: {otp}")

        request.session["otp_user_id"] = user.id
        messages.success(request, "OTP sent to your email.")
        return redirect("verify_otp")

    return render(request, "signup.html")


def verify_otp_view(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
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

        messages.success(request, "Account verified. You can now log in.")
        return redirect("login")

    return render(request, "verify_otp.html")


def resend_otp_view(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please login again.")
        return redirect("login")

    user = User.objects.get(id=user_id)
    recent_otp_exists = OTPVerification.objects.filter(
        user=user,
        purpose="signup",
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).exists()

    if recent_otp_exists:
        messages.warning(request, "Please wait before requesting a new OTP.")
        return redirect("verify_otp")

   
    OTPVerification.objects.filter(
        user=user,
        purpose="signup",
        is_verified=False
    ).update(is_verified=True)

    otp = generate_otp()

    OTPVerification.objects.create(
        user=user,
        otp=otp,
        purpose="signup",
        expires_at=OTPVerification.get_expiry_time()
    )

    print(f"RESEND OTP for {user.email}: {otp}")
    messages.success(request, "OTP resent successfully.")
    return redirect("verify_otp")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("login")

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        if user.is_blocked:
            messages.error(request, "Your account has been blocked.")
            return redirect("login")

        if not user.is_active:
            # Rate limit OTP resend
            recent_otp_exists = OTPVerification.objects.filter(
                user=user,
                purpose="signup",
                created_at__gte=timezone.now() - timedelta(minutes=1)
            ).exists()

            if recent_otp_exists:
                messages.warning(request, "Please wait before requesting a new OTP.")
                return redirect("login")

            # Invalidate all previous unverified OTPs
            OTPVerification.objects.filter(
                user=user,
                purpose="signup",
                is_verified=False
            ).update(is_verified=True)

            # User not verified → resend OTP
            otp = generate_otp()
            OTPVerification.objects.create(
                user=user,
                otp=otp,
                purpose="signup",
                expires_at=OTPVerification.get_expiry_time()
            )

            print(f"LOGIN OTP RESENT for {user.email}: {otp}")
            request.session["otp_user_id"] = user.id
            messages.warning(request, "Account not verified. OTP resent.")
            return redirect("verify_otp")

        login(request, user)
        messages.success(request, "Logged in successfully.")
        return redirect("home")

    return render(request, "login.html")

from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    user = request.user
    return render(request, "profile.html", {"user": user})


@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        # Basic validation
        if phone and len(phone) < 10:
            messages.error(request, "Phone number must be at least 10 digits.")
            return redirect("edit_profile")

        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone if phone else None
        user.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "edit_profile.html")

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Email is required.")
            return redirect("forgot_password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            #  Security: don’t reveal user existence
            messages.success(
                request,
                "If this email exists, an OTP has been sent."
            )
            return redirect("login")

        if user.is_blocked:
            messages.error(request, "Your account has been blocked.")
            return redirect("login")

        #  Rate-limit OTP
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

        #  Invalidate old forgot-password OTPs
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

        print(f"FORGOT PASSWORD OTP for {user.email}: {otp}")

        request.session["otp_user_id"] = user.id
        request.session["otp_purpose"] = "forgot_password"

        messages.success(request, "OTP sent to your email.")
        return redirect("verify_forgot_otp")

    return render(request, "forgot_password.html")


def verify_forgot_otp_view(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please try again.")
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

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

        messages.success(request, "OTP verified. Set a new password.")
        return redirect("reset_password")

    return render(request, "verify_forgot_otp.html")

def reset_password_view(request):
    user_id = request.session.get("otp_user_id")
    purpose = request.session.get("otp_purpose")

    if not user_id or purpose != "forgot_password":
        messages.error(request, "Session expired. Please try again.")
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("reset_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        user.set_password(password)
        user.save()

        #  Cleanup
        OTPVerification.objects.filter(
            user=user,
            purpose="forgot_password"
        ).delete()

        request.session.pop("otp_user_id", None)
        request.session.pop("otp_purpose", None)

        messages.success(request, "Password reset successful. Please log in.")
        return redirect("login")

    return render(request, "reset_password.html")
