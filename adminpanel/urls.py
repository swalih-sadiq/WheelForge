from django.urls import path

from adminpanel.views import (
    admin_login_view,
    admin_logout_view,
    admin_dashboard_view,
    admin_user_list_view,
    admin_block_user_view,
    admin_unblock_user_view,
    admin_confirm_block_user_view,
    admin_confirm_unblock_user_view,
)

urlpatterns = [
    path('login/', admin_login_view, name='admin-login'),
    path('logout/', admin_logout_view, name='admin-logout'),
    path('dashboard/', admin_dashboard_view, name='admin-dashboard'),

    path('users/', admin_user_list_view, name='admin-user-list'),
    path('users/block/<uuid:uuid>/', admin_block_user_view, name='admin-block-user'),
    path('users/unblock/<uuid:uuid>/', admin_unblock_user_view, name='admin-unblock-user'),

    path('users/block/<uuid:uuid>/confirm/', admin_confirm_block_user_view, name='admin-confirm-block-user'),
    path('users/unblock/<uuid:uuid>/confirm/', admin_confirm_unblock_user_view, name='admin-confirm-unblock-user'),
]