# Generated by Django 4.2.6 on 2023-12-14 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0006_alter_document_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='author',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='uploaded_by',
            field=models.CharField(default=2, max_length=100),
            preserve_default=False,
        ),
    ]
