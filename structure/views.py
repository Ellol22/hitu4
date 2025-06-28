from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

from accounts.models import Student
from grades.models import StudentGrade, GradeSheet
from structure.models import (
    StudentStructure,
    StudentStatusChoices,
    AcademicYearChoices,
    SemesterChoices,
)
from courses.models import StudentCourse  # موديل يربط الطالب بالمواد، لتحديث المواد تلقائيًا


# --- مساعدات لترقية السنة والسمستر ---
def next_semester(current_semester):
    if current_semester == SemesterChoices.FIRST:
        return SemesterChoices.SECOND
    return SemesterChoices.FIRST


def next_year(current_year):
    mapping = {
        AcademicYearChoices.FIRST: AcademicYearChoices.SECOND,
        AcademicYearChoices.SECOND: AcademicYearChoices.THIRD,
        AcademicYearChoices.THIRD: AcademicYearChoices.FOURTH,
        AcademicYearChoices.FOURTH: AcademicYearChoices.FOURTH,  # آخر سنة تظل كما هي
    }
    return mapping.get(current_year, AcademicYearChoices.FIRST)


# --- دالة لتحديد الترم الحالي للطالب بناءً على تاريخ التسجيل ---
def determine_current_semester_by_registration(student: Student):
    registration_date = student.user.date_joined.date()  # افتراض أن هذا تاريخ تسجيل الحساب

    year = registration_date.year
    start_second_semester = datetime(year, 2, 1).date()
    start_third_semester = datetime(year, 7, 1).date()

    if start_second_semester <= registration_date < start_third_semester:
        return SemesterChoices.SECOND
    else:
        return SemesterChoices.FIRST


# --- دالة تحديث مواد الطالب عند ترحيلها للسنة الجديدة ---
def transfer_failed_courses_to_new_year(student: Student, failed_courses):
    """
    تضيف المواد الساقطة إلى ترم السنة الجديدة ترم أول
    """
    try:
        structure = StudentStructure.objects.get(student=student)
    except StudentStructure.DoesNotExist:
        return {"error": "StudentStructure not found"}

    new_year = next_year(structure.year)
    new_semester = SemesterChoices.FIRST

    for course in failed_courses:
        # إضافة المادة للطالب في السنة الجديدة ترم أول
        # هذا يعتمد على موديل StudentCourse الذي يربط الطالب بالمواد
        StudentCourse.objects.update_or_create(
            student=student,
            course=course,
            defaults={"year": new_year, "semester": new_semester},
        )

    # تحديث الهيكل الأكاديمي للطالب للسنة الجديدة ترم أول
    structure.year = new_year
    structure.semester = new_semester
    structure.save()

    return {"message": "Failed courses transferred to new academic year semester 1"}


# --- دالة لفحص نتائج السمر بعد انتهاء الامتحانات ---
def check_summer_results(student: Student):
    summer_failed_courses = []
    summer_passed_courses = []

    grades = StudentGrade.objects.filter(student=student)
    for grade in grades:
        total_score = grade.total_score or 0
        full_score = grade.grade_sheet.full_score or 100
        final_score = grade.final_exam_score or 0

        if total_score >= 0.5 * full_score and final_score >= 0.4 * full_score:
            summer_passed_courses.append(grade.grade_sheet.course)
        else:
            summer_failed_courses.append(grade.grade_sheet.course)

    return len(summer_passed_courses), len(summer_failed_courses), summer_failed_courses


# --- الدالة الأساسية لتحديث حالة الطالب حسب المواد الساقطة قبل السمر ---
def update_student_structure(student: Student):
    try:
        structure = StudentStructure.objects.get(student=student)
    except StudentStructure.DoesNotExist:
        return {"error": "StudentStructure not found for student " + student.user.username}

    failed_courses = []
    grades = StudentGrade.objects.filter(student=student)
    for grade in grades:
        total_score = grade.total_score or 0
        full_score = grade.grade_sheet.full_score or 100
        final_score = grade.final_exam_score or 0

        if total_score < 0.6 * full_score or final_score < 0.4 * full_score:
            failed_courses.append(grade.grade_sheet.course)

    failed_count = len(failed_courses)

    if failed_count == 0:
        structure.status = StudentStatusChoices.PASSED
        structure.save()
        return {
            "student": student.user.username,
            "status": structure.status,
            "failed_courses": [],
            "note": "Student passed all subjects.",
        }

    if failed_count < 3:
        structure.status = StudentStatusChoices.SUMMER
        structure.save()
        return {
            "student": student.user.username,
            "status": structure.status,
            "failed_courses": [c.name for c in failed_courses],
            "year": structure.year,
            "semester": structure.semester,
            "note": "Student entered summer course for failed subjects.",
        }

    # 3 مواد أو أكثر سقط فيهم
    structure.status = StudentStatusChoices.SUMMER
    structure.save()
    return {
        "student": student.user.username,
        "status": structure.status,
        "failed_courses": [c.name for c in failed_courses],
        "year": structure.year,
        "semester": structure.semester,
        "note": "Student entered summer course for many failed subjects, waiting for summer results.",
    }


# --- دالة لتقييم نتائج السمر بعد انتهاء فترة السمر ---
def finalize_after_summer(student: Student):
    try:
        structure = StudentStructure.objects.get(student=student)
    except StudentStructure.DoesNotExist:
        return {"error": "StudentStructure not found for student " + student.user.username}

    num_passed, num_failed, failed_courses_after_summer = check_summer_results(student)

    if num_failed == 0:
        # نجح في كل مواد السمر → ترقي سنة أو ترم
        structure.status = StudentStatusChoices.PASSED
        if structure.semester == SemesterChoices.FIRST:
            structure.semester = SemesterChoices.SECOND
        else:
            structure.year = next_year(structure.year)
            structure.semester = SemesterChoices.FIRST
        structure.save()
        return {"message": "Student passed all summer courses and progressed.", "status": structure.status}

    if num_failed < 3:
        # ترحيل المواد الساقطة للسنة الجديدة ترم أول مع تحديث المواد
        structure.status = StudentStatusChoices.PASSED
        result = transfer_failed_courses_to_new_year(student, failed_courses_after_summer)
        return {
            "message": "Student failed some summer courses but less than 3. Materials moved to new academic year semester 1.",
            "failed_courses": [c.name for c in failed_courses_after_summer],
            "status": structure.status,
            "year": structure.year,
            "semester": structure.semester,
            "transfer_result": result,
        }

    # سقط في 3 مواد أو أكثر في السمر → يعيد السنة على المواد الساقطة
    if num_failed >= 3:
        structure.status = StudentStatusChoices.RETAKE_YEAR
        structure.save()
        return {
            "message": "Student failed 3 or more summer courses and must retake the year.",
            "failed_courses": [c.name for c in failed_courses_after_summer],
            "status": structure.status,
        }


# --- إضافة تحديد الترم عند إنشاء حساب الطالب (مثال) ---
def create_student_structure_on_registration(student: Student):
    semester = determine_current_semester_by_registration(student)
    structure, created = StudentStructure.objects.get_or_create(
        student=student,
        defaults={
            "year": AcademicYearChoices.FIRST,
            "semester": semester,
            "status": StudentStatusChoices.ACTIVE,
        },
    )
    return structure


# --- جزء الـ CRON أو التحديث التلقائي حسب التاريخ ---
from django.apps import AppConfig
from django.utils import timezone
import datetime


class StructureConfig(AppConfig):
    name = "structure"

    def ready(self):
        from accounts.models import Student
        from structure.views import (
            update_student_structure,
            finalize_after_summer,
        )

        today = timezone.now().date()

        # التواريخ اللي فيها ترقية تلقائية
        run_dates = {
            datetime.date(today.year, 2, 1): "first_semester",
            datetime.date(today.year, 7, 1): "second_semester",
            datetime.date(today.year, 9, 1): "summer_finalize",
        }

        if today in run_dates:
            action = run_dates[today]
            print(f"[CRON] Running {action} updates for {today}")

            students = Student.objects.all()
            for student in students:
                try:
                    if action in ["first_semester", "second_semester"]:
                        result = update_student_structure(student)
                    elif action == "summer_finalize":
                        result = finalize_after_summer(student)

                    print(f"[{action.upper()}] {student.user.username}: {result}")
                except Exception as e:
                    print(f"[ERROR] {student.user.username}: {e}")
        else:
            print(f"[SKIP] Today {today} is not in the scheduled update list.")
