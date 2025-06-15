# courses/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import Course, Quiz, Assignment
from .serializers import QuizSerializer, AssignmentSerializer
from accounts.models import Doctor, Student

# Custom permission to check if user is a Doctor
def is_doctor(user):
    return hasattr(user, 'doctor')

# Custom permission to check if user is enrolled in a course
def is_enrolled_in_course(user, course):
    if is_doctor(user):
        return course.doctor == user.doctor or course.section_assistants.filter(assistant=user.doctor).exists()
    elif hasattr(user, 'student'):
        return course.studentcourse_set.filter(student=user.student).exists()
    return False




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_courses(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    courses = request.user.doctor.get_my_courses()


    response_data = {
        'courses': [
            {'courseCode': c.id, 'courseName': c.name}
            for c in courses
        ]
    }

# اطبع في التيرمنال
    print("✅ Response Data:", response_data)

    return Response(response_data)



import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Quiz
from .serializers import QuizSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def staff_quizzes(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    # اطبع الريكويست في POST
    if request.method == 'POST':
        if request.content_type != 'application/json':
            print(f"❗ Unsupported Content-Type: {request.content_type}")
            return Response({"detail": "Content-Type must be application/json"}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        print("📥 Incoming Request Data:")
        print(json.dumps(request.data, indent=4, ensure_ascii=False))


        serializer = QuizSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data

            # اطبع الريسبونس
            print("📤 Outgoing Response Data:")
            print(json.dumps(response_data, indent=4, ensure_ascii=False))

            return Response(response_data, status=status.HTTP_201_CREATED)

        print("❌ Validation Errors:")
        print(json.dumps(serializer.errors, indent=4, ensure_ascii=False))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # اطبع الريسبونس في GET
    elif request.method == 'GET':
        quizzes = Quiz.objects.filter(course__in=request.user.doctor.get_my_courses())
        serializer = QuizSerializer(quizzes, many=True)
        response_data = serializer.data

        print("📤 GET Response Data:")
        print(json.dumps(response_data, indent=4, ensure_ascii=False))

        return Response(response_data)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_quiz_detail(request, quiz_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        if not is_enrolled_in_course(request.user, quiz.course):
            return Response({"detail": "You are not authorized to access this quiz."}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            serializer = QuizSerializer(quiz)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = QuizSerializer(quiz, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            quiz.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except ObjectDoesNotExist:
        return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def staff_assignments(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        assignments = Assignment.objects.filter(course__in=request.user.doctor.get_my_courses())
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = AssignmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_assignment_detail(request, assignment_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
        if not is_enrolled_in_course(request.user, assignment.course):
            return Response({"detail": "You are not authorized to access this assignment."}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            serializer = AssignmentSerializer(assignment)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = AssignmentSerializer(assignment, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            assignment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except ObjectDoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_quizzes_notify(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    quiz_id = request.data.get('quizId')
    course_id = request.data.get('course')
    try:
        quiz = Quiz.objects.get(id=quiz_id, course_id=course_id)
        if not is_enrolled_in_course(request.user, quiz.course):
            return Response({"detail": "You are not authorized to notify for this quiz."}, status=status.HTTP_403_FORBIDDEN)
        # Implement notification logic (e.g., send emails or push notifications to students)
        return Response({"detail": "Notification sent successfully."}, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        return Response({"detail": "Quiz or course not found."}, status=status.HTTP_404_NOT_FOUND)