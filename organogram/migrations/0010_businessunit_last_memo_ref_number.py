# Generated by Django 4.2.6 on 2024-01-16 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organogram', '0009_alter_externalcustomer_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='last_memo_ref_number',
            field=models.IntegerField(default=0),
        ),
    ]
