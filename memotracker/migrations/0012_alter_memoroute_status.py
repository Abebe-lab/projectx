# Generated by Django 4.2.6 on 2024-01-27 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memotracker', '0011_memoroute_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memoroute',
            name='status',
            field=models.CharField(choices=[('notseen', 'Not Seen'), ('seen', 'Seen')], default='notseen'),
        ),
    ]
