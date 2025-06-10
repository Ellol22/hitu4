from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from courses.models import Course
from courses.serializers import CourseSerializer  # لازم يكون موجود
from .models import UploadFile
from .serializers import UploadFileSerializer
from accounts.models import Doctor, Student

# 1️⃣ دكتور يجيب مواده (الكورسات اللي هو مسؤول عنها)
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def doctor_courses_view(request):
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return Response({"detail": "User is not a doctor."}, status=status.HTTP_403_FORBIDDEN)

    courses = Course.objects.filter(doctor=doctor)
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)


# 2️⃣ دكتور يرفع ملف على كورس معين
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_upload_file_view(request):
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return Response({"detail": "User is not a doctor."}, status=status.HTTP_403_FORBIDDEN)

    course_id = request.data.get('course')
    if not course_id:
        return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

    # تحقق أن الدكتور هو المسؤول عن الكورس
    if course.doctor != doctor:
        return Response({"detail": "You are not allowed to upload to this course."}, status=status.HTTP_403_FORBIDDEN)

    serializer = UploadFileSerializer(data=request.data)
    if serializer.is_valid():
        upload_file = serializer.save(uploaded_by=request.user, course=course)
        return Response({
            'id': upload_file.id,
            'course': {
                'id': upload_file.course.id,
                'name': upload_file.course.name
            },
            'file_url': upload_file.file.url,
            'uploaded_at': upload_file.uploaded_at
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 3️⃣ طالب يجيب الكورسات (المواد) اللي مسجل فيها
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_courses_view(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return Response({"detail": "User is not a student."}, status=status.HTTP_403_FORBIDDEN)

    # جلب الكورسات المرتبطة بالطالب من StudentCourse
    courses = Course.objects.filter(studentcourse__student=student).distinct()
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)


# 4️⃣ طالب يجيب ملفات كورس معين
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_files_view(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return Response({"detail": "User is not a student."}, status=status.HTTP_403_FORBIDDEN)

    course_id = request.query_params.get('course_id')
    if not course_id:
        return Response({"detail": "course_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    # تحقق أن الطالب مسجل في الكورس
    from courses.models import StudentCourse
    if not StudentCourse.objects.filter(student=student, course_id=course_id).exists():
        return Response({"detail": "You are not enrolled in this course."}, status=status.HTTP_403_FORBIDDEN)

    # جلب ملفات الرفع الخاصة بالكورس
    files = UploadFile.objects.filter(course_id=course_id)
    files_serializer = UploadFileSerializer(files, many=True)

    # جلب بيانات الكورس للرد
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'course': {
            'id': course.id,
            'name': course.name
        },
        'files': files_serializer.data
    })
