# Generated by Django 5.2.1 on 2025-06-08 22:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_remove_course_academic_year_remove_course_department_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='drive_link',
        ),
    ]
