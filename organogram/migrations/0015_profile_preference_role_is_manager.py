# Generated by Django 4.2.6 on 2024-02-28 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organogram', '0014_profile_password_set_role_is_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='preference',
            field=models.JSONField(default=dict),
        ),
    ]
