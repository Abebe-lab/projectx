# Generated by Django 4.2.6 on 2023-12-06 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memotracker', '0007_alter_memo_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memo',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('approved', 'Approved'), ('outgoing', 'Outgoing'), ('incoming', 'Incoming'), ('closed', 'Closed')], default='draft'),
        ),
    ]
