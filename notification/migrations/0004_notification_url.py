# Generated by Django 4.2.6 on 2024-03-18 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0003_notification_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='url',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
