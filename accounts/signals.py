from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(social_account_added)
def set_auth_provider(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    provider = sociallogin.account.provider
    user.auth_provider = provider
    user.save()
