from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.utils import timezone

from accounts.models import OTPVerification
from .utils import generate_otp

User = get_user_model()


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

        print(f"SIGNUP OTP for {email}: {otp}")

        request.session["otp_user_id"] = user.id
        messages.success(request, "OTP sent to your email.")
        return redirect("verify_otp")

    return render(request, "signup.html")


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
                return redirect("login")

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

            print(f"LOGIN OTP RESENT for {user.email}: {otp}")
            request.session["otp_user_id"] = user.id
            messages.warning(
                request,
                "Account not verified. OTP resent."
            )
            return redirect("verify_otp")

        login(request, user)
        messages.success(request, "Logged in successfully.")
        return redirect("home")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")
