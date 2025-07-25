# Generated by Django 5.2.4 on 2025-07-22 09:48

import core.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_customuser_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=core.utils.profile_pics_upload_to),
        ),
    ]
