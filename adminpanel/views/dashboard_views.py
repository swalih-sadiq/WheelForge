from django.shortcuts import render

from accounts.models import User
from core.decorators import admin_required

@admin_required
def admin_dashboard_view(request):
    total_users = User.objects.count()
    blocked_users = User.objects.filter(
        is_blocked=True
    ).count()
    active_users = total_users - blocked_users

    return render(
        request,
        'adminpanel/dashboard.html',
        {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
        },
    )
