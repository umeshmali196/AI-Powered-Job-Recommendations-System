from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    headline = models.CharField(max_length=255, blank=True)
    preferred_location = models.CharField(max_length=120, blank=True)
    summary = models.TextField(blank=True)
    skills = models.TextField(blank=True, null=True)
    github_username = models.CharField(max_length=255, blank=True)
    github_name = models.CharField(max_length=255, blank=True)
    github_profile_url = models.URLField(blank=True)
    github_avatar_url = models.URLField(blank=True)
    github_bio = models.TextField(blank=True)
    github_public_repos = models.PositiveIntegerField(blank=True, null=True)
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
