from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from courses.models import Course, StudentCourse
from .models import Task, Submission
from .serializers import TaskSerializer, SubmissionSerializer

# ------------------ TASK VIEWS -------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list_create(request):
    user = request.user

    # ---------- GET ----------
    if request.method == 'GET':
        # الدكتور يشوف التاسكات اللي هو كريّتها
        if hasattr(user, 'doctor'):
            courses = Course.objects.filter(doctor=user.doctor)
            tasks = Task.objects.filter(course__in=courses, created_by=user).order_by('-due_date')
            serializer = TaskSerializer(tasks, many=True, context={'request': request})
            return Response(serializer.data)

        # الطالب يشوف التاسكات الخاصة بمواده فقط
        elif hasattr(user, 'student'):
            student_courses = StudentCourse.objects.filter(student=user.student).values_list('course', flat=True)
            tasks = Task.objects.filter(course__in=student_courses).order_by('-due_date')
            serializer = TaskSerializer(tasks, many=True, context={'request': request})
            return Response(serializer.data)

        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    # ---------- POST ----------
    elif request.method == 'POST':
        if not hasattr(user, 'doctor'):
            return Response({"detail": "Only doctors can create tasks."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            course_id = serializer.validated_data.get('course').id
            if not Course.objects.filter(id=course_id, doctor=user.doctor).exists():
                return Response({"detail": "You can only create tasks for your own courses."}, status=status.HTTP_403_FORBIDDEN)

            serializer.save(created_by=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail(request, pk):
    user = request.user
    task = get_object_or_404(Task, pk=pk)

    if not hasattr(user, 'doctor') or task.created_by != user:
        return Response({"detail": "Not allowed to access this task."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TaskSerializer(task, data=request.data, context={'request': request})
        if serializer.is_valid():
            course = serializer.validated_data.get('course')
            if course.doctor != user.doctor:
                return Response({"detail": "You can only assign tasks to your own courses."}, status=status.HTTP_403_FORBIDDEN)

            serializer.save(created_by=user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ------------------ SUBMISSION VIEWS -------------------

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def submission_detail(request, pk):
    user = request.user
    submission = get_object_or_404(Submission, pk=pk)

    if not hasattr(user, 'student') or submission.student != user:
        return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)

    elif request.method == 'PUT':
        task = submission.task
        if timezone.now().date() > task.due_date:
            return Response({"detail": "Deadline passed. Cannot update submission."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmissionSerializer(submission, data=request.data)
        if serializer.is_valid():
            serializer.save(student=user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if timezone.now().date() > submission.task.due_date:
            return Response({"detail": "Deadline passed. Cannot delete submission."}, status=status.HTTP_400_BAD_REQUEST)

        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submission_create(request):
    user = request.user

    if not hasattr(user, 'student'):
        return Response({"detail": "Only students can submit tasks."}, status=status.HTTP_403_FORBIDDEN)

    serializer = SubmissionSerializer(data=request.data)
    if serializer.is_valid():
        task = serializer.validated_data.get('task')

        # تأكد الطالب في المادة
        if not StudentCourse.objects.filter(student=user.student, course=task.course).exists():
            return Response({"detail": "You are not enrolled in this course."}, status=status.HTTP_403_FORBIDDEN)

        # تأكد لسه قبل الديدلاين
        if timezone.now().date() > task.due_date:
            return Response({"detail": "Deadline has passed. Submission not allowed."}, status=status.HTTP_400_BAD_REQUEST)

        # نحفظ التسليم باسم الطالب الحالي
        serializer.save(student=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
