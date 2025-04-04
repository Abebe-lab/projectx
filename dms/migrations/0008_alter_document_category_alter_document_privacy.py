# Generated by Django 4.2.6 on 2023-12-25 19:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0007_document_author_document_uploaded_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='categories', to='dms.documentcategory'),
        ),
        migrations.AlterField(
            model_name='document',
            name='privacy',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='Private', max_length=15),
        ),
    ]
