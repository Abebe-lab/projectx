# Generated by Django 4.2.6 on 2024-03-19 12:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notification', '0004_notification_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='recipient',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='status',
        ),
        migrations.CreateModel(
            name='NotificationRecipient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('unread', 'Unread'), ('read', 'Read')], default='unread')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notification.notification')),
                ('recipient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notify_to', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
