from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from accounts.models import User
from .decorators import admin_required

# Create your views here.

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin-dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is None or not user.is_superuser:
            messages.error(request, 'Invalid admin credentials,')
            return redirect('admin-login')
        
        login(request,user)
        return redirect ('admin-dashboard')
    return render(request, 'adminpanel/login.html')

@admin_required
def admin_dashboard_view(request):
    total_users = User.objects.count()
    blocked_users = User.objects.filter(is_blocked=True).count()
    active_users = total_users - blocked_users 

    return render(request, 'adminpanel/dashboard.html', {
        'total_users': total_users,
        'active_users': active_users,
        'blocked_users': blocked_users,
    },
    )

def admin_logout_view(request):
    logout(request)
    return redirect('admin-login')


@admin_required
def admin_user_list_view(request):
    query =  request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-created_at')

    if query:
        users = users.filter(email__icontains=query)

    paginator = paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'adminpanel/user_list.html', 
                  {
                      'page_obj': page_obj,
                      'query': query,
                  },
                  )

@admin_required 
@require_POST
def admin_block_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'You cannot block yourself.')
        return redirect('admin-user-list')
    
    user.is_blocked = True 
    user.save()

    messages.success(request, f'{user.email} has been blocked.')
    return redirect('admin-user-list')


@admin_required
@require_POST 
def admin_unblock_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    user.is_blocked = False 
    user.save()

    messages.success(request, f'{user.email} has been blocked.')
    return redirect('admin-user-list')




@admin_required
def admin_confirm_block_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user ==request.user:
        return render(request, 'errors/403.html', {
            'title': 'Action Denied',
            'message': 'You cannot block yourself.',
        },
        status=403,
        )
    
    return render(request, 'adminpanel/confirm_block.html', {'target_user':user},)

@admin_required
def admin_confirm_unblock_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    return render (request, 'adminpanel/cofirm_unblock.html', {'target_user': user},)
