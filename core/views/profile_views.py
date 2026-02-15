from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from accounts.models import Address, User

from core.decorators import user_required


# @login_required
# def profile_view(request, uuid):
#     if request.user.uuid != uuid:
#         messages.error(request, 'Unauthorized access.')
#         return redirect('profile', uuid=request.user.uuid)
    
#     return render(
#         request,
#         "profile.html",
#         {"user": request.user}
#     )
@never_cache
@login_required
@user_required
def profile_view(request, uuid):
    if request.user.uuid != uuid:
        return redirect("home")

    user = request.user
    addresses = Address.objects.filter(user=request.user)

    return render(
        request,
        "profile.html",   
        {'user': user, "addresses": addresses}
        )

@login_required
@user_required
def upload_profile_image_view(request, uuid):
    if request.user.uuid != uuid:
        messages.error(request, 'Unauthorized access')
        return redirect('profile', uuid=request.user.uuid)
    
    if request.method == "POST":
        image = request.FILES.get("profile_image")

        if not image:
            messages.error(request, "No image selected.")
            return redirect("profile", uuid=request.user.uuid)

        if image.size > 2 * 1024 * 1024:
            messages.error(
                request,
                "Image too large (max 2MB)."
            )
            return redirect("profile", uuid=request.user.uuid)

        request.user.profile_image = image
        request.user.save()

        messages.success(
            request,
            "Profile image updated."
        )
        return redirect("profile", uuid=request.user.uuid)


@login_required
@user_required
def edit_profile_view(request, uuid):
    if request.user.uuid != uuid:
        messages.error(request, 'Unauthorized access')
        return redirect('edit_profile', uuid=request.user.uuid)

    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        new_email = request.POST.get('email', '').strip().lower()

        if first_name and not first_name.isalpha():
            messages.error(request,"First name must contain only alphabets.")
            return redirect("edit_profile", uuid=request.user.uuid)
        
        if last_name and not last_name.isalpha():
            messages.error(request,"Last name must contain only alphabets.")
            return redirect("edit_profile", uuid=request.user.uuid)

        if phone:
            if not phone.isdigit() or len(phone) != 10:
                messages.error(request,"Phone number must contain exactly 10 digits.")
                return redirect("edit_profile", uuid=request.user.uuid)

        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone if phone else None
        user.save()

        # -------- HANDLE EMAIL CHANGE --------
        if new_email and new_email != user.email:

            if User.objects.filter(email=new_email).exists():
                messages.error(request, "This email is already in use.")
                return redirect("edit_profile", uuid=user.uuid)


            request.session["email_change_new_email"] = new_email

            return redirect("request-email-change")

        messages.success(request,"Profile updated successfully.")
        return redirect("profile", uuid=request.user.uuid)

    return render(request, "edit_profile.html")
