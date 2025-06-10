from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Student
from courses.models import Course, StudentCourse
from structure.models import AcademicYearChoices, SemesterChoices, StudentStructure

# ترتيب سنوات الدراسة عشان نقدر نستخدمه للمقارنة
year_order = {
    'First': 1,
    'Second': 2,
    'Third': 3,
    'Fourth': 4,
}

# ترتيب الترم عشان نقدر نقارن
semester_order = {
    'First': 1,
    'Second': 2,
}

@receiver(post_save, sender=Student)
def auto_assign_courses_to_student(sender, instance, **kwargs):
    student = instance

    if not student.structure:
        return

    # جلب الهيكل الحالي
    current_year = student.structure.year
    current_semester = student.structure.semester

    # تحديد كل سنوات الدراسة والترمات اللي أقل أو تساوي الهيكل الحالي
    valid_structures = []
    for year, y_val in year_order.items():
        for sem, s_val in semester_order.items():
            # اذا السنة اقل من السنة الحالية
            if y_val < year_order[current_year]:
                valid_structures.append((year, sem))
            # اذا السنة تساوي السنة الحالية والسمستر اقل او يساوي الحالي
            elif y_val == year_order[current_year] and s_val <= semester_order[current_semester]:
                valid_structures.append((year, sem))

    # جلب المواد لكل الهيكل اللي حددناه
    matched_courses = Course.objects.filter(
        structure__in=[
            StudentStructure.objects.get(year=year, semester=sem, department=student.structure.department)
            for year, sem in valid_structures
        ]
    )

    # إضافة المواد الجديدة التي لم تُربط بعد مع الطالب
    for course in matched_courses:
        if not StudentCourse.objects.filter(student=student, course=course).exists():
            StudentCourse.objects.create(student=student, course=course)
