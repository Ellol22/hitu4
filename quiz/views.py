from rest_framework.decorators import api_view, permission_classes , parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import AssignmentFile, Course, Quiz, Assignment, QuizSubmission, QuizAnswer, Submission
from .serializers import AssignmentFileSerializer, QuizSerializer, AssignmentSerializer
from accounts.models import Doctor, Student
import json
from rest_framework.parsers import MultiPartParser, FormParser


# Custom permission to check if user is a Doctor
def is_doctor(user):
    return hasattr(user, 'doctor')

# Custom permission to check if user is enrolled in a course
def is_enrolled_in_course(user, course):
    if not hasattr(user, 'student'):
        return False
    return course.stucourses.filter(student=user.student).exists()


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
    print("✅ Response Data:", response_data)
    return Response(response_data)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser])  # دعم multipart/form-data
@permission_classes([IsAuthenticated])
def staff_quizzes(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        # التحقق من نوع المحتوى
        if 'multipart/form-data' not in request.content_type and request.content_type != 'application/json':
            print(f"❗ Unsupported Content-Type: {request.content_type}")
            return Response({"detail": "Content-Type must be application/json or multipart/form-data"}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        print("📥 Incoming Request Data:")
        print(request.data)

        # التحقق من وجود course_id في البيانات
        course_id = request.data.get('course')
        if not course_id:
            print("❌ No course ID provided")
            return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
            if course.doctor != request.user.doctor:
                print("❌ Doctor not allowed to upload to this course")
                return Response({"detail": "You are not allowed to upload to this course."}, status=status.HTTP_403_FORBIDDEN)
        except Course.DoesNotExist:
            print("❌ Course not found")
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        # معالجة بيانات الكويز
        quiz_serializer = QuizSerializer(data=request.data, context={'request': request})
        if quiz_serializer.is_valid():
            quiz = quiz_serializer.save()
            response_data = quiz_serializer.data

            # إذا كان فيه ملف مرفوع
            if 'file' in request.FILES:
                file_data = {
                    'file': request.FILES['file']
                }
                file_serializer = AssignmentFileSerializer(data=file_data)
                if file_serializer.is_valid():
                    # حفظ الملف مع ربطه بالكويز
                    upload_file = file_serializer.save(quiz=quiz, assignment=None)  # لو هتستخدمي حقل quiz في AssignmentFile
                    response_data['file_url'] = upload_file.file.url
                    print("✅ File uploaded successfully")
                else:
                    print("❌ File serializer errors:", file_serializer.errors)
                    return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            print("📤 Outgoing Response Data:")
            print(json.dumps(response_data, indent=4, ensure_ascii=False))
            return Response(response_data, status=status.HTTP_201_CREATED)

        print("❌ Quiz validation errors:")
        print(json.dumps(quiz_serializer.errors, indent=4, ensure_ascii=False))
        return Response(quiz_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        quizzes = Quiz.objects.filter(course__in=request.user.doctor.get_my_courses())
        serializer = QuizSerializer(quizzes, many=True)
        response_data = []
        for quiz_data in serializer.data:
            start_time = quiz_data.get('startTime')
            end_time = quiz_data.get('endTime')
            if start_time and end_time:
                from datetime import datetime
                start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 60  # Duration in minutes
                quiz_data['duration'] = duration
            # إضافة روابط الملفات المرتبطة بالكويز
            quiz = Quiz.objects.get(id=quiz_data['id'])
            files = AssignmentFile.objects.filter(quiz=quiz)  # لو هتستخدمي حقل quiz
            quiz_data['files'] = [{'id': f.id, 'file_url': f.file.url} for f in files]
            response_data.append(quiz_data)

        print("📤 GET Response Data:")
        print(json.dumps(response_data, indent=4, ensure_ascii=False))
        return Response(response_data)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from quiz.models import Quiz
from quiz.serializers import QuizSerializer
from django.core.exceptions import PermissionDenied
import json
from datetime import datetime

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_quiz_detail(request, quiz_id):
    print("📥 Incoming Request:")
    print(json.dumps({
        "method": request.method,
        "user": str(request.user),
        "user_id": request.user.id,
        "data": request.data if request.method in ['PUT'] else None,
    }, indent=4, ensure_ascii=False))

    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        print(f"❌ Quiz with id={quiz_id} not found.")
        return Response({"detail": f"Quiz with id={quiz_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    # ✅ التحقق إن الدكتور هو صاحب المادة
    if quiz.course.doctor != request.user.doctor:
        return Response({"detail": "You are not authorized to access this quiz."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = QuizSerializer(quiz)
        response_data = serializer.data
        start_time = response_data.get('startTime')
        end_time = response_data.get('endTime')
        if start_time and end_time:
            from datetime import datetime
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = (end - start).total_seconds() / 60
            response_data['duration'] = duration

        print("📤 Outgoing Response:")
        print(json.dumps(response_data, indent=4, ensure_ascii=False, default=str))
        return Response(response_data)

    elif request.method == 'PUT':
        serializer = QuizSerializer(quiz, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            start_time = response_data.get('startTime')
            end_time = response_data.get('endTime')
            if start_time and end_time:
                from datetime import datetime
                start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 60
                response_data['duration'] = duration
            print("✅ Quiz updated successfully")
            print("📤 Outgoing Response:")
            print(json.dumps(response_data, indent=4, ensure_ascii=False, default=str))
            return Response(response_data)
        else:
            print("❌ Validation Errors:")
            print(json.dumps(serializer.errors, indent=4, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        quiz.delete()
        print("🗑️ Quiz deleted successfully.")
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser])  # عشان يستقبل ملفات
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
            assignment = serializer.save()

            # ✅ حفظ الملف لو موجود
            if 'file' in request.FILES:
                AssignmentFile.objects.create(
                    assignment=assignment,
                    file=request.FILES['file']
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_assignment_detail(request, assignment_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        print(f"❌ Assignment with id={assignment_id} not found.")
        return Response({"detail": f"Assignment with id={assignment_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    # تحقق إن الدكتور الحالي هو صاحب المادة المرتبط بيها التكليف
    if assignment.course.doctor != request.user.doctor:
        return Response({"detail": "You are not authorized to access this assignment."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = AssignmentSerializer(assignment)
        print("📤 GET Response Data:")
        print(json.dumps(serializer.data, indent=4, ensure_ascii=False, default=str))
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AssignmentSerializer(assignment, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            print("✅ Assignment updated successfully")
            print("📤 Outgoing Response:")
            print(json.dumps(serializer.data, indent=4, ensure_ascii=False, default=str))
            return Response(serializer.data)
        else:
            print("❌ Validation Errors:")
            print(json.dumps(serializer.errors, indent=4, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        assignment.delete()
        print("🗑️ Assignment deleted successfully.")
        return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def staff_quizzes_notify(request):
#     if not is_doctor(request.user):
#         return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

#     quiz_id = request.data.get('quizId')
#     course_id = request.data.get('course')
#     try:
#         quiz = Quiz.objects.get(id=quiz_id, course_id=course_id)
#         if not is_enrolled_in_course(request.user, quiz.course):
#             return Response({"detail": "You are not authorized to notify for this quiz."}, status=status.HTTP_403_FORBIDDEN)
#         # Implement notification logic (e.g., send emails or push notifications to students)
#         return Response({"detail": "Notification sent successfully."}, status=status.HTTP_200_OK)
#     except ObjectDoesNotExist:
#         return Response({"detail": "Quiz or course not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_courses(request):
    print("📥 Incoming Request Data:")
    print(json.dumps({
        "user": str(request.user),
        "user_id": request.user.id,
        "user_type": "Student" if hasattr(request.user, 'student') else "Other"
    }, indent=4, ensure_ascii=False))

    if not hasattr(request.user, 'student'):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    student_courses = request.user.student.student_courses.select_related('course').all()
    response_data = [
        {
            "courseCode": sc.course.id,
            "courseName": sc.course.name
        } for sc in student_courses
    ]

    # print("📤 Outgoing Response Data:")
    # print(json.dumps(response_data, indent=4, ensure_ascii=False))
    return Response(response_data)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
import json
from .models import Quiz, QuizSubmission, QuizAnswer
from .serializers import QuizSerializer


def is_enrolled_in_course(user, course):
    return course.stucourses.filter(student=user.student).exists()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_quizzes(request):
    print("📥 Incoming Request Data:")
    print(json.dumps({
        "user": str(request.user),
        "user_id": request.user.id,
        "user_type": "Student" if hasattr(request.user, 'student') else "Other"
    }, indent=4, ensure_ascii=False))

    if not hasattr(request.user, 'student'):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    student_courses_ids = request.user.student.student_courses.values_list('course_id', flat=True)
    quizzes = Quiz.objects.filter(course_id__in=student_courses_ids)
    now = timezone.now()

    quiz_data = []
    for quiz in quizzes:
        submission = QuizSubmission.objects.filter(quiz=quiz, student=request.user.student).first()

        # Determine quiz status and score for this student
        if submission:
            status_value = submission.status
            score = submission.score
        elif quiz.start_time <= now <= quiz.end_time:
            status_value = 'not_started'
            score = None
        else:
            continue  # Skip if quiz is not available and no submission

        duration = (quiz.end_time - quiz.start_time).total_seconds() / 60  # Duration in minutes

        quiz_data.append({
            "quiz_id": quiz.id,
            "title": quiz.title,
            "course": quiz.course.name,
            "start_time": quiz.start_time,
            "end_time": quiz.end_time,
            "duration": duration,
            "status": status_value,
            "score": score
        })

    print("📤 Outgoing Response Data:")
    print(json.dumps(quiz_data, indent=4, ensure_ascii=False, default=str))
    return Response(quiz_data)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def student_quiz_detail(request, quiz_id):
    if not hasattr(request.user, 'student'):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

    if not is_enrolled_in_course(request.user, quiz.course):
        return Response({"detail": "You are not enrolled in the course for this quiz."}, status=status.HTTP_403_FORBIDDEN)

    now = timezone.now()
    if not (quiz.start_time <= now <= quiz.end_time):
        return Response({"detail": "Quiz not available right now."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = QuizSerializer(quiz)
        response_data = serializer.data

        start_time = response_data.get('startTime')
        end_time = response_data.get('endTime')

        if start_time and end_time:
            from datetime import datetime
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = (end - start).total_seconds() / 60
            response_data['duration'] = duration
        else:
            response_data['duration'] = None

        print("📤 GET Response Data:")
        print(json.dumps(response_data, indent=4, ensure_ascii=False, default=str))
        return Response(response_data)

    elif request.method == 'POST':
        if QuizSubmission.objects.filter(quiz=quiz, student=request.user.student).exists():
            return Response({"detail": "You have already submitted this quiz."}, status=status.HTTP_400_BAD_REQUEST)

        answers = request.data.get("answers", [])
        questions = quiz.questions.order_by('id')

        if len(answers) != questions.count():
            return Response({"detail": "Incomplete answers."}, status=status.HTTP_400_BAD_REQUEST)

        submission = QuizSubmission.objects.create(student=request.user.student, quiz=quiz)

        for index, answer in enumerate(answers):
            question = questions[index]
            QuizAnswer.objects.create(
                submission=submission,
                question=question,
                selected_option=answer
            )

        submission.calculate_score()
        submission.status = "ended"
        submission.save()

        return Response({"detail": "Quiz submitted successfully.", "score": submission.score})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_assignments(request):
    print("\n📥 Incoming Request Data:")
    print(json.dumps({
        "user": str(request.user),
        "user_id": request.user.id,
        "user_type": "Student" if hasattr(request.user, 'student') else "Other"
    }, indent=4, ensure_ascii=False))

    if not hasattr(request.user, 'student'):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    student_courses_ids = request.user.student.student_courses.values_list('course_id', flat=True)
    assignments = Assignment.objects.filter(course_id__in=student_courses_ids)

    assignment_data = []
    for assignment in assignments:
        file_obj = assignment.files.first()
        file_url = request.build_absolute_uri(file_obj.file.url) if file_obj else None

        print(f"📎 Assignment {assignment.id} File URL: {file_url}")

        assignment_data.append({
            "assignment_id": assignment.id,
            "title": assignment.title,
            "course": assignment.course.name,
            "deadline": assignment.deadline,
            "file": file_url
        })

    print("\n📤 Outgoing Response Data:")
    print(json.dumps(assignment_data, indent=4, ensure_ascii=False, default=str))

    return Response(assignment_data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_submit_assignment(request, assignment_id):
    if not hasattr(request.user, 'student'):
        return Response({"detail": "Only students can submit assignments."}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
        if timezone.now() > assignment.deadline:
            return Response({"detail": "Deadline has passed."}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist('files')
        if not files:
            return Response({"detail": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        for file in files:
            Submission.objects.create(
                assignment=assignment,
                student=request.user.student,
                file=file
            )

        return Response({"detail": "Assignment submitted successfully."}, status=status.HTTP_201_CREATED)

    except Assignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def student_delete_submission(request, submission_id):
    if not hasattr(request.user, 'student'):
        return Response({"detail": "Only students can delete submissions."}, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = Submission.objects.get(id=submission_id, student=request.user.student)
        if timezone.now() > submission.assignment.deadline:
            return Response({"detail": "Deadline has passed."}, status=status.HTTP_403_FORBIDDEN)

        submission.file.delete()
        submission.delete()
        return Response({"detail": "Submission deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    except Submission.DoesNotExist:
        return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)