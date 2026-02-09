from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse

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

        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address_line_1 = request.POST.get("address_line_1", "").strip()
        address_line_2 = request.POST.get("address_line_2", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        if not full_name.isalpha():
            messages.error(request, "Full name must contain only alphabets.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")



        if not address_line_1.isalpha():
            messages.error(request, "Address Line 1 must contain only alphabets.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")



        if address_line_2 and not address_line_2.isalpha():
            messages.error(request, "Address Line 2 must contain only alphabets.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")


        if not city.isalpha():
            messages.error(request, "City must contain only alphabets.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")


        if not state.isalpha():
            messages.error(request, "State must contain only alphabets.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")


        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")


        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Pincode must be exactly 6 digits.")
            return redirect(f"{reverse('profile', kwargs={'uuid': request.user.uuid})}?section=addresses")



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
def edit_address_view(request, uuid):
    address = get_object_or_404(
        Address,
        uuid=uuid,
        user=request.user
    )

    if request.method == "POST":
        is_default = bool(request.POST.get("is_default"))

        if is_default:
            Address.objects.filter(
                user=request.user,
                is_default=True
            ).exclude(id=address.id).update(is_default=False)

        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address_line_1 = request.POST.get("address_line_1", "").strip()
        address_line_2 = request.POST.get("address_line_2", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        if not full_name.isalpha():
            messages.error(request, "Full name must contain only alphabets.")
            return redirect("edit-address", uuid=uuid)

        if not address_line_1.isalpha():
            messages.error(request, "Address Line 1 must contain only alphabets.")
            return redirect("edit-address", uuid=uuid)

        if address_line_2 and not address_line_2.isalpha():
            messages.error(request, "Address Line 2 must contain only alphabets.")
            return redirect("edit-address", uuid=uuid)

        if not city.isalpha():
            messages.error(request, "City must contain only alphabets.")
            return redirect("edit-address", uuid=uuid)

        if not state.isalpha():
            messages.error(request, "State must contain only alphabets.")
            return redirect("edit-address", uuid=uuid)

        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect("edit-address", uuid=uuid)

        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Pincode must be exactly 6 digits.")
            return redirect("edit-address", uuid=uuid)

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
def delete_address_view(request, uuid):
    address = get_object_or_404(
        Address,
        uuid=uuid,
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
