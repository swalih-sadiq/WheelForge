from django.urls import path
from accounts.views import (
    request_email_change_view,
    verify_email_change_otp_view,
    address_list_view,
    add_address_view,
    edit_address_view,
    delete_address_view,
)


urlpatterns=[
    path('email-change/', request_email_change_view, name='request-email-change'),
    path('email-change/verify', verify_email_change_otp_view, name='verify-email-change-otp'),

    path('pofile/addresses/', address_list_view, name='address-list'),
    path('profile/addresses/add/', add_address_view, name='add-address'),
    path('profile/addresses/edit/<uuid:uuid>/', edit_address_view, name='edit-address'),
    path('profile/addresses/delete/<uuid:uuid>/', delete_address_view, name='delete-address'),
]