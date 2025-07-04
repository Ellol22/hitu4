# Generated by Django 5.2.1 on 2025-06-08 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0002_rename_score_studentgrade_total_score_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradesheet',
            name='final_exam_full_score',
            field=models.FloatField(default=50),
        ),
        migrations.AddField(
            model_name='gradesheet',
            name='midterm_full_score',
            field=models.FloatField(default=20),
        ),
        migrations.AddField(
            model_name='gradesheet',
            name='section_exam_full_score',
            field=models.FloatField(default=15),
        ),
        migrations.AddField(
            model_name='gradesheet',
            name='year_work_full_score',
            field=models.FloatField(default=15),
        ),
        migrations.AddField(
            model_name='studentgrade',
            name='is_passed',
            field=models.BooleanField(default=False),
        ),
    ]
