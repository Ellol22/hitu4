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

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def manage_course_grades(request, course_name):
    user = request.user

    if not is_doctor(user):
        return Response({"detail": "You do not have access permission."}, status=status.HTTP_403_FORBIDDEN)

    doctor = user.doctor

    try:
        course = Course.objects.get(name=course_name, doctor=doctor)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found or not assigned to you."}, status=status.HTTP_404_NOT_FOUND)

    try:
        grade_sheet = GradeSheet.objects.get(course=course)
    except GradeSheet.DoesNotExist:
        return Response({"detail": "No grade sheet for this course."}, status=status.HTTP_404_NOT_FOUND)

    # -------- GET: عرض درجات كل الطلبة --------
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

    # -------- PATCH: تعديل GradeSheet أو درجات طالب --------
    elif request.method == 'PATCH':
        if request.data.get('update_gradesheet'):
            # تعديل مكونات GradeSheet
            allowed_fields = [
                'full_score',
                'final_exam_full_score',
                'midterm_full_score',
                'section_exam_full_score',
                'year_work_full_score'
            ]
            for field in allowed_fields:
                if field in request.data:
                    setattr(grade_sheet, field, request.data[field])
            try:
                grade_sheet.save()
                return Response({"detail": "GradeSheet updated successfully."})
            except ValidationError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # تعديل درجة طالب
        username = request.data.get('username')
        if not username:
            return Response({"detail": "username is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(user__username=username)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        student_grade, created = StudentGrade.objects.get_or_create(
            grade_sheet=grade_sheet,
            student=student
        )

        serializer = StudentGradeSerializer(student_grade, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
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
    return Response(courses_data)
