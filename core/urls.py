from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('login/', views.login_view, name='login'),
]