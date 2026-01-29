from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='admin-login'),
    path('logout/', views.admin_logout_view, name='admin-logout'),
    path('dashboard/',views.admin_dashboard_view, name='admin-dashboard')    
]