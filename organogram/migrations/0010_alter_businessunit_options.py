# Generated by Django 4.2.6 on 2024-01-18 07:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organogram', '0009_alter_externalcustomer_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='businessunit',
            options={'ordering': ['name_en']},
        ),
    ]
