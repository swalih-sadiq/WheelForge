from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from adminpanel.decorators import admin_required


def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin-dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is None or not user.is_superuser:
            messages.error(
                request,
                'Invalid admin credentials,'
            )
            return redirect('admin-login')

        login(request, user)
        return redirect('admin-dashboard')

    return render(request, 'adminpanel/login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin-login')
