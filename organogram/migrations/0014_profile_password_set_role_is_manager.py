# Generated by Django 4.2.6 on 2024-02-22 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organogram', '0013_alter_profile_profile_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='password_set',
            field=models.BooleanField(default=False),
        ),
    ]
