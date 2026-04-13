from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver

from .social import sync_github_profile


@receiver(social_account_added)
def sync_added_social_account(request, sociallogin, **kwargs):
    if sociallogin.account.provider == 'github':
        sync_github_profile(sociallogin.user.profile, sociallogin.account)


@receiver(social_account_updated)
def sync_updated_social_account(request, sociallogin, **kwargs):
    if sociallogin.account.provider == 'github':
        sync_github_profile(sociallogin.user.profile, sociallogin.account)
