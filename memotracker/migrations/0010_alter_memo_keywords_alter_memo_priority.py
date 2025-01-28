# Generated by Django 4.2.6 on 2023-12-25 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memotracker', '0009_alter_memo_status_alter_memoattachment_memo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memo',
            name='keywords',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='memo',
            name='priority',
            field=models.CharField(choices=[('high', 'High'), ('mid', 'Medium'), ('low', 'Low')], default='medium'),
        ),
    ]
