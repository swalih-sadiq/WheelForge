from functools import wraps
from django.shortcuts import redirect, render

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin-login')
        
        if not request.user.is_superuser:
            return render(request, 'errors/403.html', 
                          {
                              'title': 'Access Denied',
                              'message': 'This page is restricted to administartors only.'
                          },
                          status=403
                          )
        return view_func(request, *args, **kwargs)
    return _wrapped_view