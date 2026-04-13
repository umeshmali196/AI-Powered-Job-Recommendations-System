from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import TestCase

from .social import sync_github_profile


class GitHubProfileSyncTests(TestCase):
    def test_sync_github_profile_updates_candidate_profile_fields(self):
        user = User.objects.create_user(username='candidate', password='secret123')
        profile = user.profile

        github_account = SocialAccount.objects.create(
            user=user,
            provider='github',
            uid='1001',
            extra_data={
                'login': 'octocat',
                'name': 'The Octocat',
                'html_url': 'https://github.com/octocat',
                'avatar_url': 'https://avatars.githubusercontent.com/u/1001?v=4',
                'bio': 'Building better developer experiences.',
                'public_repos': 8,
            },
        )

        sync_github_profile(profile, github_account)
        profile.refresh_from_db()

        self.assertEqual(profile.github_username, 'octocat')
        self.assertEqual(profile.github_name, 'The Octocat')
        self.assertEqual(profile.github_profile_url, 'https://github.com/octocat')
        self.assertEqual(profile.github_public_repos, 8)

    def test_sync_github_profile_returns_none_when_not_connected(self):
        user = User.objects.create_user(username='nontech', password='secret123')
        profile = user.profile

        synced_account = sync_github_profile(profile)

        self.assertIsNone(synced_account)
        self.assertEqual(profile.github_username, '')
