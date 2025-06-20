# Generated by Django 5.2.1 on 2025-06-14 12:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_alter_doctor_structures_alter_student_structure'),
        ('courses', '0008_alter_course_structure_alter_studentcourse_course_and_more'),
        ('grades', '0003_gradesheet_final_exam_full_score_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradesheet',
            name='course',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='courses.course'),
        ),
        migrations.AlterField(
            model_name='gradesheet',
            name='doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teacher', to='accounts.doctor'),
        ),
    ]
