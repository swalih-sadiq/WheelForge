from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import OTPVerification
from core.utils.otp import generate_otp
from core.utils.email import send_otp_email
from core.utils.validators import validate_signup_data
from core.utils.validators import validate_login_data
from core.utils.logger import app_logger, security_logger


User = get_user_model()

@never_cache
def signup_view(request):
    if request.method == "POST":

        #  Clear previous OTP session
        request.session.pop('otp_user_id', None)
        request.session.pop('otp_purpose', None)

        # Validate data
        errors = validate_signup_data(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request, error)
            return redirect('signup')

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")
        
        name_parts = full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        #  Create inactive user first
        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            first_name =first_name,
            last_name=last_name,
            is_active=False
        )

        app_logger.info(f"New user created (inactive): {user.email} (ID: {user.id})")

        #  Invalidate previous signup OTPs (if any)
        OTPVerification.objects.filter(
            user=user,
            purpose='signup',
            is_verified=False
        ).update(is_verified=True)

        #  Create OTP in DB
        otp = generate_otp()
        OTPVerification.objects.create(
            user=user,
            otp=otp,
            purpose='signup',
            expires_at=OTPVerification.get_expiry_time()
        )

        #  Store minimal session authority
        request.session['otp_user_id'] = user.id
        request.session['otp_purpose'] = 'signup'

        #  Send email
        send_otp_email(email, otp, 'signup')

        messages.success(request, "OTP sent to your email.")
        return redirect("verify_otp")

    return render(request, "signup.html")

@never_cache
def login_view(request):
    if request.method == "POST":
        
        request.session.pop("otp_user_id", None)
        request.session.pop("otp_purpose", None)
        request.session.pop("otp_created_at", None)

        errors = validate_login_data(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request, error)
            return redirect('login')
    
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        
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
            messages.error(request,"Your account is not verified. Please verify your email first.")
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