# Generated by Django 4.2.6 on 2023-12-13 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0003_alter_document_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(upload_to='Documents'),
        ),
    ]
