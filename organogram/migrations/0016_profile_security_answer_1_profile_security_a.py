# Generated by Django 4.2.6 on 2024-03-26 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organogram', '0015_profile_preference_role_is_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='security_answer_1',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_answer_2',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_answer_3',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_question_1',
            field=models.CharField(default='Your birth year', max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_question_2',
            field=models.CharField(blank=True, default="Your grandmother's name", max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_question_3',
            field=models.CharField(blank=True, default='Name of your elementary school', max_length=100, null=True),
        ),
    ]
