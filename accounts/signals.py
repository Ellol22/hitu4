from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from accounts.models import Student
from courses.models import Course, StudentCourse

# نحتفظ بالـ structure القديم قبل الحفظ
@receiver(pre_save, sender=Student)
def remember_old_structure(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_student = Student.objects.get(pk=instance.pk)
            instance._old_structure = old_student.structure
        except Student.DoesNotExist:
            instance._old_structure = None
    else:
        instance._old_structure = None

@receiver(post_save, sender=Student)
def auto_assign_courses_to_student(sender, instance, **kwargs):
    student = instance

    if not student.structure:
        return

    # لو الـ structure اتغير أو الطالب جديد (مفيهوش ID قبل كدا)
    if not hasattr(student, '_old_structure') or student.structure != student._old_structure:
        # امسح المواد القديمة
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
