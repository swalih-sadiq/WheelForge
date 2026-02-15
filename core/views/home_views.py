from django.shortcuts import render,redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required



@never_cache
def home_view(request):
    # if not request.user.is_authenticated or request.user.is_superuser:
    #     return redirect("login")
    return render(request, 'home.html')

