from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_profile_headline_profile_phone_number_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="profile_photo",
            field=models.ImageField(blank=True, null=True, upload_to="profile_photos/"),
        ),
    ]
