from django.urls import path
from . import views

urlpatterns=[
    path('email-change/', views.request_email_change_view, name='request-email-change'),
    path('email-change/verify', views.verify_email_change_otp_view, name='verify-email-change-otp'),

    path('addresses/', views.address_list_view, name='address-list'),
    path('addresses/add/', views.add_address_view, name='add-address'),
    path('addresses/edit/<int:address_id>/', views.edit_address_view, name='edit-address'),
    path('addresses/delete/<int:address_id>/', views.delete_address_view, name='delete-address'),
]