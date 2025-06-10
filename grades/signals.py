from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import StudentCourse, Course
from grades.models import GradeSheet, StudentGrade

# لما الطالب يتسجل في مادة، نضيفه في StudentGrade تلقائيًا
@receiver(post_save, sender=StudentCourse)
def add_student_to_gradesheet(sender, instance, created, **kwargs):
    if not created:
        return

    student = instance.student
    course = instance.course

    grade_sheet, _ = GradeSheet.objects.get_or_create(course=course)

    exists = StudentGrade.objects.filter(grade_sheet=grade_sheet, student=student).exists()
    if not exists:
        StudentGrade.objects.create(
            grade_sheet=grade_sheet,
            student=student,
            total_score=0  # الدرجة الافتراضية
        )

# لما الدكتور يتسجل أو يتغير في Course، يتحدث تلقائيًا في GradeSheet
@receiver(post_save, sender=Course)
def sync_doctor_to_gradesheet(sender, instance, **kwargs):
    course = instance
    doctor = course.doctor

    grade_sheet, _ = GradeSheet.objects.get_or_create(course=course)

    if grade_sheet.doctor != doctor:
        grade_sheet.doctor = doctor
        grade_sheet.save()