# Generated by Django 5.2.1 on 2025-06-18 18:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_quizsubmission_submission_quizanswer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quiz',
            name='duration',
        ),
    ]
