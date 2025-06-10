# signals.py في app الحسابات (accounts)
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from accounts.models import Student
from courses.models import Course, StudentCourse

@receiver(post_save, sender=Student)
def auto_assign_courses_to_student(sender, instance, **kwargs):
    student = instance

    # لو مفيش structure مش هيكمل
    if not student.structure:
        return

    # امسح كل المواد المرتبطة بالطالب الأول
    StudentCourse.objects.filter(student=student).delete()

    # هات المواد اللي ليها نفس القسم والسنة والترم
    matched_courses = Course.objects.filter(
        structure__department=student.structure.department,
        structure__year=student.structure.year,
        structure__semester=student.structure.semester
    )

    # اربط الطالب بالمواد دي
    for course in matched_courses:
        StudentCourse.objects.create(student=student, course=course)
