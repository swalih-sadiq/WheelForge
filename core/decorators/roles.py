from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('admin-login')
        
        if getattr(request.user, 'is_blocked', False):
            messages.error(request, 'Your account has been blocked.')
            return redirect('login')
        
        if not request.user.is_superuser:
            return render(
                request,
                'errors/403.html',
                {
                    'title': 'Access Denied',
                    'message': 'This page is restricted to administrators only.'
                },
                status=403
            )
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('login')

        if getattr(request.user, 'is_blocked', False):
            messages.error(request, 'Your account has been blocked.')
            return redirect('login')

        if not request.user.is_active:
            messages.error(request, 'Your account is active.')
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return _wrapped_view        