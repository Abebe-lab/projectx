# Generated by Django 4.2.6 on 2025-01-19 12:29

from django.db import migrations, models
import django.db.models.deletion
import organogram.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('dms', '0027_remove_document_content_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='owner_business_unit',
        ),
        migrations.RemoveField(
            model_name='document',
            name='owner_external_customer',
        ),
        migrations.RemoveField(
            model_name='document',
            name='owner_user',
        ),
        migrations.AddField(
            model_name='document',
            name='content_type',
            field=organogram.models.ContentTypeModelField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype', verbose_name='Owner Type'),
        ),
        migrations.AddField(
            model_name='document',
            name='object_id',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
