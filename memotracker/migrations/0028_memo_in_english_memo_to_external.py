# Generated by Django 4.2.6 on 2024-04-11 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memotracker', '0027_alter_memoroute_destination_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='memo',
            name='in_english',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='memo',
            name='to_external',
            field=models.BooleanField(default=False),
        ),
    ]
