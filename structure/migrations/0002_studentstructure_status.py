# Generated by Django 5.2.1 on 2025-06-08 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentstructure',
            name='status',
            field=models.CharField(choices=[('passed', 'Passed'), ('summer', 'Summer Course'), ('retake_year', 'Retake Year')], default='passed', max_length=20),
        ),
    ]
