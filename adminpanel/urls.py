from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='admin-login'),
    path('logout/', views.admin_logout_view, name='admin-logout'),
    path('dashboard/',views.admin_dashboard_view, name='admin-dashboard'),

    path('users/', views.admin_user_list_view, name='admin-user-list'),
    path('users/block/<int:user_id>/', views.admin_block_user_view, name='admin-block-user'),
    path('users/unblock/<int:user_id>/', views.admin_unblock_user_view, name='admin-unblock-user'),    
]