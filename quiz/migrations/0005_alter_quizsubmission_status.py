# Generated by Django 5.2.1 on 2025-06-18 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_quizsubmission_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quizsubmission',
            name='status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('ended', 'Ended')], default='not_started', max_length=20),
        ),
    ]
