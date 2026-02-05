from django.urls import path

from core.views import (
    home_view,
    signup_view,
    login_view,
    logout_view,
    verify_otp_view,
    resend_otp_view,
    profile_view,
    upload_profile_image_view,
    edit_profile_view,
    forgot_password_view,
    verify_forgot_otp_view,
    reset_password_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('verify-forgot-otp/', verify_forgot_otp_view, name='verify_forgot_otp'),
    path('reset-password/', reset_password_view, name='reset_password'),

    path('profile/<uuid:uuid>/', profile_view, name='profile'),
    path('profile/<uuid:uuid>/image/', upload_profile_image_view, name='upload-profile-image'),
    path('profile/<uuid:uuid>/edit/', edit_profile_view, name='edit_profile'),
]