from allauth.socialaccount.models import SocialAccount


def get_github_account(user):
    return SocialAccount.objects.filter(user=user, provider='github').first()


def sync_github_profile(profile, github_account=None):
    github_account = github_account or get_github_account(profile.user)
    if not github_account:
        return None

    extra_data = github_account.extra_data or {}
    profile.github_username = extra_data.get('login', '') or profile.github_username
    profile.github_name = extra_data.get('name', '') or profile.github_name
    profile.github_profile_url = extra_data.get('html_url', '') or profile.github_profile_url
    profile.github_avatar_url = extra_data.get('avatar_url', '') or profile.github_avatar_url
    profile.github_bio = extra_data.get('bio', '') or profile.github_bio
    profile.github_public_repos = extra_data.get('public_repos')
    profile.save(
        update_fields=[
            'github_username',
            'github_name',
            'github_profile_url',
            'github_avatar_url',
            'github_bio',
            'github_public_repos',
        ]
    )
    return github_account
