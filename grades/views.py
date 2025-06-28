from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from grades.models import GradeSheet, StudentGrade
from courses.models import Course
from accounts.models import Student
from grades.serializers import  StudentGradeSerializer

def is_doctor(user):
    return hasattr(user, 'doctor')

def is_student(user):
    return hasattr(user, 'student')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_grades(request):
    user = request.user

    if is_student(user):
        student = user.student
        grades = StudentGrade.objects.filter(student=student)
        serializer = StudentGradeSerializer(grades, many=True)
        
        # print("Student grades response:", serializer.data)
        
        return Response(serializer.data)

    print("Permission denied response")  # ← دي في حالة مش طالب
    return Response(
        {"detail": "You do not have permission to view grades."},
        status=status.HTTP_403_FORBIDDEN
    )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import Course, GradeSheet, StudentGrade, Student
from .serializers import StudentGradeSerializer


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_course_grades(request, course_name):
    user = request.user

    # التأكد من أن المستخدم لديه علاقة بدكتور
    try:
        doctor = user.doctor
    except AttributeError:
        return Response({"detail": "Only doctors are allowed to access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    # التأكد من أن الدكتور مسؤول عن هذه المادة
    try:
        course = Course.objects.get(name=course_name, doctor=doctor)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found or not assigned to you."}, status=status.HTTP_404_NOT_FOUND)

    # التأكد من وجود ورقة درجات للمادة
    try:
        grade_sheet = GradeSheet.objects.get(course=course)
    except GradeSheet.DoesNotExist:
        return Response({"detail": "No grade sheet for this course."}, status=status.HTTP_404_NOT_FOUND)

    # ----------- GET: عرض درجات كل الطلبة -----------
    if request.method == 'GET':
        student_grades = StudentGrade.objects.filter(grade_sheet=grade_sheet)
        serializer = StudentGradeSerializer(student_grades, many=True)

        grade_sheet_data = {
            'full_score': grade_sheet.full_score,
            'final_exam_full_score': grade_sheet.final_exam_full_score,
            'midterm_full_score': grade_sheet.midterm_full_score,
            'section_exam_full_score': grade_sheet.section_exam_full_score,
            'year_work_full_score': grade_sheet.year_work_full_score,
        }

        return Response({
            'grade_sheet': grade_sheet_data,
            'student_grades': serializer.data
        })

    # ----------- PATCH: تعديل ورقة الدرجات أو درجات طالب معين -----------
    elif request.method == 'PATCH':
        data = request.data
        print(data)

        # تحديث إعدادات ورقة الدرجات
        if data.get('update_gradesheet'):
            allowed_fields = [
                'full_score',
                'final_exam_full_score',
                'midterm_full_score',
                'section_exam_full_score',
                'year_work_full_score'
            ]
            for field in allowed_fields:
                if field in data:
                    setattr(grade_sheet, field, data[field])

            try:
                grade_sheet.save()
                return Response({"detail": "Grade sheet updated successfully."})
            except ValidationError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # تحديث درجات طالب
        student_name = data.get('student_name')
        if not student_name:
            return Response({"detail": "Field 'student_name' is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(name__iexact=student_name)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found with this name."}, status=status.HTTP_404_NOT_FOUND)

        student_grade, _ = StudentGrade.objects.get_or_create(
            grade_sheet=grade_sheet,
            student=student
        )

        serializer = StudentGradeSerializer(student_grade, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print(serializer.data)
            return Response(serializer.data)
            

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_courses(request):
    user = request.user

    if not is_doctor(user):
        return Response({"detail": "You do not have access permission."}, status=status.HTTP_403_FORBIDDEN)

    doctor = user.doctor
    courses = Course.objects.filter(doctor=doctor)
    courses_data = [{"id": c.id, "name": c.name} for c in courses]

    # print("[Doctor Courses Response]:", courses_data)  # ✅ ده اللي بيطبع في التيرمنال/server log

    return Response(courses_data)



#################################################################################
# views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg
from grades.models import StudentGrade
from accounts.models import Student

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_students_by_section_year(request):
    result = {}

    students = Student.objects.all()

    for student in students:
        grades = StudentGrade.objects.filter(student=student)

        if not grades.exists():
            continue

        avg_percentage = grades.aggregate(avg=Avg("percentage"))["avg"]

        key = f"{student.section.name} - Year {student.academic_year}"

        if key not in result:
            result[key] = []

        result[key].append({
            "full_name": student.full_name,
            "student_id": student.id,
            "avg_percentage": round(avg_percentage or 0, 2)
        })

    # نرتب ونجيب أول 10 بس
    for key in result:
        result[key] = sorted(result[key], key=lambda x: x["avg_percentage"], reverse=True)[:10]

    return Response(result)



#################################################################################

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Doctor
from courses.models import Course
from grades.models import GradeSheet

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_courses_statistics(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'أنت مش دكتور'}, status=403)

    statistics = []

    courses = doctor.courses.all()

    for course in courses:
        try:
            grade_sheet = course.courses  # related_name في OneToOneField
            student_grades = grade_sheet.student_grades.all()
            passed_count = student_grades.filter(is_passed=True).count()
            failed_count = student_grades.filter(is_passed=False).count()

            statistics.append({
                "course_name": course.name,
                "structure": f"{course.structure.section.name} - Year {course.structure.year}",
                "passed": passed_count,
                "failed": failed_count
            })

        except GradeSheet.DoesNotExist:
            # لو مفيش grade sheet للمادة
            statistics.append({
                "course_name": course.name,
                "structure": f"{course.structure.section.name} - Year {course.structure.year}",
                "passed": 0,
                "failed": 0
            })

    return Response(statistics)
