from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from accounts.models import User
from adminpanel.decorators import admin_required


@admin_required
def admin_user_list_view(request):
    query = request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-created_at')

    if query:
        users = users.filter(
            email__icontains=query
        )


    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'adminpanel/user_list.html',
        {
            'page_obj': page_obj,
            'query': query,
        },
    )


@admin_required
@require_POST
def admin_block_user_view(request, user_id):
    user = get_object_or_404(
        User,
        id=user_id
    )

    if user == request.user:
        messages.error(
            request,
            'You cannot block yourself.'
        )
        return redirect('admin-user-list')

    user.is_blocked = True
    user.save()

    messages.success(
        request,
        f'{user.email} has been blocked.'
    )
    return redirect('admin-user-list')

@admin_required
@require_POST
def admin_unblock_user_view(request, user_id):
    user = get_object_or_404(
        User,
        id=user_id
    )

    user.is_blocked = False
    user.save()

    messages.success(
        request,
        f'{user.email} has been blocked.'
    )
    return redirect('admin-user-list')


@admin_required
def admin_confirm_block_user_view(request, user_id):
    user = get_object_or_404(
        User,
        id=user_id
    )

    if user == request.user:
        return render(
            request,
            'errors/403.html',
            {
                'title': 'Action Denied',
                'message': 'You cannot block yourself.',
            },
            status=403,
        )

    return render(
        request,
        'adminpanel/confirm_block.html',
        {
            'target_user': user
        },
    )

@admin_required
def admin_confirm_unblock_user_view(request, user_id):
    user = get_object_or_404(
        User,
        id=user_id
    )

    return render(
        request,
        'adminpanel/cofirm_unblock.html',
        {
            'target_user': user
        },
    )
