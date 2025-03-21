# Generated by Django 4.2.6 on 2024-11-05 20:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dms', '0010_shareddocument_document_shared_with'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='privacy',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='private', max_length=15),
        ),
        migrations.AlterField(
            model_name='document',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents_uploaded', to=settings.AUTH_USER_MODEL),
        ),
    ]
