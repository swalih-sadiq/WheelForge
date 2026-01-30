from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-forgot-otp/', views.verify_forgot_otp_view, name='verify_forgot_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/image/', views.upload_profile_image_view, name='upload-profile-image'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
]