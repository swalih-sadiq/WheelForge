import time
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

from .models import Address

# Create your views here.

def generate_otp():
    return str(random.randint(100000,999999))



def clear_email_change_session(request):
    keys = [
        "email_change_otp",
        "email_change_new_email",
        "email_change_time",
        "email_change_attempts",
    ]
    for key in keys:
        request.session.pop(key, None)


@login_required
def request_email_change_view(request):
    if request.method == "POST":
        new_email = request.POST.get("email")

        if not new_email:
            messages.error(request, "Email is required.")
            return redirect("request-email-change")

        if new_email == request.user.email:
            messages.error(request, "New email must be different.")
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

        # ---------- SEND OTP TO NEW EMAIL ----------
        send_mail(
            subject="WheelForge – Email Change OTP",
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

        # ---------- OTP EXPIRY (5 minutes) ----------
        if int(time.time()) - otp_time > 300:
            messages.error(request, "OTP expired.")
            clear_email_change_session(request)
            return redirect("request-email-change")

        if entered_otp != session_otp:
            messages.error(request, "Invalid OTP.")
            return redirect("verify-email-change-otp")

        # ---------- UPDATE EMAIL ----------
        old_email = request.user.email
        request.user.email = new_email
        request.user.save()

        # ---------- NOTIFY OLD EMAIL ----------
        send_mail(
            subject="WheelForge – Email Changed",
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
        return redirect("profile")

    return render(request, "accounts/verify_email_change_otp.html")


@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses':addresses})


@login_required
def add_address_view(request):
    if request.method == "POST":
        # Check if user already has addresses
        has_addresses = Address.objects.filter(user=request.user).exists()

        is_default = bool(request.POST.get("is_default"))

        # If this is the first address, force default
        if not has_addresses:
            is_default = True

        # If setting this as default, unset others
        if is_default:
            Address.objects.filter(
                user=request.user,
                is_default=True
            ).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=request.POST.get("full_name"),
            phone=request.POST.get("phone"),
            address_line_1=request.POST.get("address_line_1"),
            address_line_2=request.POST.get("address_line_2"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            pincode=request.POST.get("pincode"),
            is_default=is_default,
        )

        messages.success(request, "Address added successfully.")
        return redirect("address-list")

    return render(request, "accounts/add_address.html")



@login_required
def edit_address_view(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    if request.method == "POST":
        is_default = bool(request.POST.get("is_default"))

        if is_default:
            Address.objects.filter(
                user=request.user,
                is_default=True
            ).exclude(id=address.id).update(is_default=False)

        address.full_name = request.POST.get("full_name")
        address.phone = request.POST.get("phone")
        address.address_line_1 = request.POST.get("address_line_1")
        address.address_line_2 = request.POST.get("address_line_2")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.pincode = request.POST.get("pincode")
        address.is_default = is_default
        address.save()

        messages.success(request, "Address updated successfully.")
        return redirect("address-list")

    return render(
        request,
        "accounts/edit_address.html",
        {"address": address}
    )



@login_required
def delete_address_view(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    was_default = address.is_default
    address.delete()

    # If default address was deleted, assign another
    if was_default:
        next_address = Address.objects.filter(
            user=request.user
        ).first()

        if next_address:
            next_address.is_default = True
            next_address.save()

    messages.success(request, "Address deleted.")
    return redirect("address-list")
