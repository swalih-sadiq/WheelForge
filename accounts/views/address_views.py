from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.models import Address 


@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def add_address_view(request):
    if request.method == "POST":
        has_addresses = Address.objects.filter(
            user=request.user
        ).exists()

        is_default = bool(request.POST.get("is_default"))

        if not has_addresses:
            is_default = True

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

        messages.success(
            request,
            "Address updated successfully."
        )
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

    if was_default:
        next_address = Address.objects.filter(
            user=request.user
        ).first()

        if next_address:
            next_address.is_default = True
            next_address.save()

    messages.success(request, "Address deleted.")
    return redirect("address-list")
