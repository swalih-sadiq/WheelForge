from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import OTPVerification
from core.utils.otp import generate_otp
from core.utils.email import send_otp_email


User = get_user_model()

@never_cache
def signup_view(request):
    if request.method == "POST":

        request.session.pop("otp_user_id", None)
        request.session.pop("otp_purpose", None)
        request.session.pop("otp_created_at", None)
        
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("signup")
        
        if "@" not in email or "." not in email:
            messages.error(request, "Enter a valid email address.")
            return redirect("signup")
        
        if len(password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters long."
            )
            return redirect("signup")
        
        if password.isdigit():
            messages.error(
                request,
                "Password cannot be entirely numeric."
            )
            return redirect("signup")
        
        if password != confirm_password:  # 🔹 ADDED
            messages.error(
                request,
                "Password and Confirm Password do not match."
            )
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

        send_otp_email(email, otp, 'signup')
        

        request.session["otp_user_id"] = user.id
        request.session['otp_purpose'] = 'signup'
        request.session['otp_created_at'] = timezone.now().isoformat()
        messages.success(request, "OTP sent to your email.")
        return redirect("verify_otp")

    return render(request, "signup.html")

@never_cache
def login_view(request):
    if request.method == "POST":

        request.session.pop("otp_user_id", None)
        request.session.pop("otp_purpose", None)
        request.session.pop("otp_created_at", None)

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("login")
        
        if len(email) > 60:
            messages.error(request, "Enter a valid email address.")
            return redirect("login")
        
        if '@' not in email or '.' not in email:
            messages.error(request, "Enter a valid email address.")
            return redirect('login')
        
        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        if user.is_blocked:
            messages.error(request, "Your account has been blocked.")
            return redirect("login")

        if not user.is_active:
            messages.error(
                request,
                "Your account is not verified. Please verify your email first."
            )
            return redirect("login")

        request.session.flush()
        login(request, user)
        messages.success(request, "Logged in successfully.")
        return redirect("home")

    return render(request, "login.html")

@never_cache
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")