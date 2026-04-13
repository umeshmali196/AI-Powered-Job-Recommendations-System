from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_profile_resume_alter_profile_skills'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='github_avatar_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='github_bio',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='github_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='profile',
            name='github_profile_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='github_public_repos',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='github_username',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
