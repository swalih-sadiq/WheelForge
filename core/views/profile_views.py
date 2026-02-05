from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def profile_view(request, uuid):
    if request.user.uuid != uuid:
        messages.error(request, 'Unauthorized access.')
        return redirect('profile', uuid=request.user.uuid)
    
    return render(
        request,
        "profile.html",
        {"user": request.user}
    )

@login_required
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
def edit_profile_view(request, uuid):
    if request.user.uuid != uuid:
        messages.error(request, 'Unauthorized access')
        return redirect('edit_profile', uuid=request.user.uuid)

    user = request.user

    if request.method == "POST":
        first_name = request.POST.get(
            "first_name", ""
        ).strip()
        last_name = request.POST.get(
            "last_name", ""
        ).strip()
        phone = request.POST.get(
            "phone", ""
        ).strip()

        if phone and len(phone) < 10:
            messages.error(
                request,
                "Phone number must be at least 10 digits."
            )
            return redirect("edit_profile", uuid=request.user.uuid)

        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone if phone else None
        user.save()

        messages.success(
            request,
            "Profile updated successfully."
        )
        return redirect("profile", uuid=request.user.uuid)

    return render(request, "edit_profile.html")
