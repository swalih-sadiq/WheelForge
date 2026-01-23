import random
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
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

    # ⏱ Rate limit (same rule everywhere)
    recent_otp_exists = OTPVerification.objects.filter(
        user=user,
        purpose="signup",
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).exists()

    if recent_otp_exists:
        messages.warning(request, "Please wait before requesting a new OTP.")
        return redirect("verify_otp")

    # ❗ Invalidate old OTPs
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
            # ⏱ Rate limit OTP resend
            recent_otp_exists = OTPVerification.objects.filter(
                user=user,
                purpose="signup",
                created_at__gte=timezone.now() - timedelta(minutes=1)
            ).exists()

            if recent_otp_exists:
                messages.warning(request, "Please wait before requesting a new OTP.")
                return redirect("login")

            # ❗ Invalidate all previous unverified OTPs
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