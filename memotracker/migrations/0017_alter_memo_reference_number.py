# Generated by Django 4.2.6 on 2024-02-01 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memotracker', '0016_merge_20240127_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memo',
            name='reference_number',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
