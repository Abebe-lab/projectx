# Generated by Django 4.2.6 on 2023-11-27 08:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0002_alter_document_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('memotracker', '0003_alter_memo_content_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemoAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment_date', models.DateTimeField(auto_now_add=True)),
                ('permission', models.CharField(choices=[('read', 'Read'), ('share', 'Share')], default='read')),
                ('attached_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='dms.document')),
                ('memo', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='memotracker.memo')),
            ],
        ),
    ]
