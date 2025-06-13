# import random, os, qrcode, json
# from datetime import datetime, timedelta
# from django.http import JsonResponse
# from django.shortcuts import render
# from django.conf import settings
# from courses.models import Course
# from django.utils import timezone
# from math import radians, sin, cos, sqrt, atan2
# from .models import QRCodeSession, LectureSession
# from schedule.models import Schedule
# from attendance.models import Attendance
# from courses.models import StudentCourse
# import face_recognition
# import pickle
# import numpy as np
# from PIL import Image
# from io import BytesIO
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework_simplejwt.authentication import JWTAuthentication

# jwt_authenticator = JWTAuthentication()

# #########################
# # Check if student is enrolled in the course of this lecture
# def check_student_enrollment(student, lecture):
#     course = lecture.course
#     return StudentCourse.objects.filter(student=student, course=course).exists()

# #########################

# # Doctor creates new lecture
# @csrf_exempt
# def create_lecture_api(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Only POST allowed'}, status=405)

#     try:
#         auth_header = request.headers.get('Authorization')
#         if not auth_header or not auth_header.startswith('Bearer '):
#             raise Exception('Authorization header missing or invalid')

#         token = auth_header.split(' ')[1]
#         validated_token = jwt_authenticator.get_validated_token(token)
#         user = jwt_authenticator.get_user(validated_token)

#         if not hasattr(user, 'is_doctor') or not user.is_doctor:
#             return JsonResponse({'error': 'Only doctors can create lectures.'}, status=403)

#         data = json.loads(request.body)
#         course_id = data.get('course_name')
#         lecture_date_str = data.get('lecture_date')
#         lecture_name = data.get('lecture_name')

#         if not course_id or not lecture_date_str or not lecture_name:
#             return JsonResponse({'error': 'course_id, lecture_date, lecture_name are required'}, status=400)

#         course = Course.objects.get(id=course_id)
#         lecture_date = datetime.strptime(lecture_date_str, '%Y-%m-%d').date()

#         lecture = LectureSession.objects.create(
#             course=course,
#             date=lecture_date,
#             name=lecture_name,
#             is_open_for_attendance=False
#         )

#         return JsonResponse({'status': 'success', 'lecture_id': lecture.id})

#     except Exception as e:
#         return JsonResponse({'error': str(e)})

# #########################

# # Doctor generates QR code for lecture
# def generate_qr_code_ajax(request, course_id):
#     course = Course.objects.get(id=course_id)
#     lecture_id = request.GET.get('lecture_id')
#     lecture = None
#     if lecture_id:
#         lecture = LectureSession.objects.filter(id=lecture_id).first()

#     random_number = random.randint(1000, 9999)

#     qr_data = {
#         'course_name': course.name,
#         'lecture_date': lecture.date.strftime('%Y-%m-%d') if lecture else '',
#         'code': random_number,
#     }
#     qr_code_data = json.dumps(qr_data)

#     qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
#     os.makedirs(qr_codes_dir, exist_ok=True)

#     filename = f"qr_code_{int(datetime.now().timestamp())}.png"
#     file_path = os.path.join(qr_codes_dir, filename)

#     qr = qrcode.make(qr_code_data)
#     qr.save(file_path)

#     qr_session = QRCodeSession.objects.create(
#         course=course,
#         lecture=lecture,
#         code=str(random_number),
#         image=f'qr_codes/{filename}',
#         is_active=True
#     )

#     # Mark lecture as open
#     if lecture:
#         lecture.is_open_for_attendance = True
#         lecture.save()

#     image_url = f"{settings.MEDIA_URL}qr_codes/{filename}"
#     return JsonResponse({'image_url': image_url})

# #########################

# # Student gets only lectures that have active QR
# def get_open_lectures_for_student(request):
#     try:
#         student = get_authenticated_student(request)
#         enrolled_courses = StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)

#         active_qr_sessions = QRCodeSession.objects.filter(
#             is_active=True,
#             created_at__gte=timezone.now() - timedelta(minutes=15),
#             course_id__in=enrolled_courses
#         ).select_related('lecture')

#         open_lectures = []
#         for qr_session in active_qr_sessions:
#             lecture = qr_session.lecture
#             if lecture:
#                 open_lectures.append({
#                     'lecture_id': lecture.id,
#                     'lecture_date': lecture.date.strftime("%Y-%m-%d"),
#                     'course_name': qr_session.course.name,
#                     'qr_image_url': f"{settings.MEDIA_URL}{qr_session.image}",
#                 })

#         return JsonResponse({'status': 'success', 'open_lectures': open_lectures})

#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': str(e)})

# #########################

# # Verify QR Code (if needed)
# def verify_qr_code(request):
#     code = request.GET.get('qr_code_data')
#     try:
#         if not code or not code.isdigit():
#             return JsonResponse({'status': 'error', 'message': 'Invalid QR Code (not numeric)'})

#         qr_session = QRCodeSession.objects.get(
#             code=int(code),
#             is_active=True,
#             created_at__gte=timezone.now() - timedelta(minutes=1)
#         )

#         return JsonResponse({
#             'status': 'success',
#             'message': 'QR Code is valid',
#             'course_name': qr_session.course.name,
#             'lecture_date': qr_session.lecture.date.strftime("%Y-%m-%d") if qr_session.lecture else None,
#             'lecture_id': qr_session.lecture.id if qr_session.lecture else None,
#         })

#     except QRCodeSession.DoesNotExist:
#         return JsonResponse({'status': 'error', 'message': 'Invalid QR Code'})

# #########################

# # Location Verification (no change)
# BUILDING_ZONES = {
#     'A': [(30.1000, 31.2980), (30.1000, 31.2990), (30.1010, 31.2990), (30.1010, 31.2980)],
#     'G': [(30.1020, 31.2950), (30.1020, 31.2960), (30.1030, 31.2960), (30.1030, 31.2950)],
#     'C': [(30.1040, 31.2970), (30.1040, 31.2980), (30.1050, 31.2980), (30.1050, 31.2970)],
#     'D': [(30.1060, 31.2990), (30.1060, 31.3000), (30.1070, 31.3000), (30.1070, 31.2990)],
#     'F': [(30.1080, 31.3010), (30.1080, 31.3020), (30.1090, 31.3020), (30.1090, 31.3010)],
# }

# def is_point_in_polygon(lat, lon, polygon):
#     x = lon
#     y = lat
#     inside = False
#     n = len(polygon)
#     p1x, p1y = polygon[0][1], polygon[0][0]
#     for i in range(n + 1):
#         p2x, p2y = polygon[i % n][1], polygon[i % n][0]
#         if min(p1y, p2y) < y <= max(p1y, p2y):
#             if x <= max(p1x, p2x):
#                 xinters = (y - p1y) * (p2x - p1x) / ((p2y - p1y) + 1e-10) + p1x
#                 if p1x == p2x or x <= xinters:
#                     inside = not inside
#         p1x, p1y = p2x, p2y
#     return inside

# #########################

# # Face APIs
# DATA_FOLDER = os.path.join(settings.BASE_DIR, 'students_data')
# os.makedirs(DATA_FOLDER, exist_ok=True)

# def get_face_encoding_from_image_file(image_file):
#     img = Image.open(image_file)
#     img = img.convert('RGB')
#     img_array = np.array(img)
#     face_locations = face_recognition.face_locations(img_array)
#     if not face_locations:
#         return None
#     encoding = face_recognition.face_encodings(img_array, face_locations)[0]
#     return encoding

# def get_authenticated_student(request):
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith('Bearer '):
#         raise Exception('Authorization header missing or invalid')

#     token = auth_header.split(' ')[1]
#     validated_token = jwt_authenticator.get_validated_token(token)
#     user = jwt_authenticator.get_user(validated_token)

#     if not hasattr(user, 'student'):
#         raise Exception('Only students can perform this action')

#     return user.student

# @csrf_exempt
# def register_face_api(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Only POST allowed'}, status=405)

#     try:
#         student = get_authenticated_student(request)
#         student_id = student.id
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=401)

#     images = [request.FILES.get(f'image{i}') for i in range(1, 4)]
#     if any(img is None for img in images):
#         return JsonResponse({'error': 'Three images (image1, image2, image3) are required'}, status=400)

#     encodings = []
#     for img in images:
#         encoding = get_face_encoding_from_image_file(img)
#         if encoding is None:
#             return JsonResponse({'error': 'No face detected in one of the images'}, status=400)
#         encodings.append(encoding)

#     file_path = os.path.join(DATA_FOLDER, f"{student_id}.pkl")
#     with open(file_path, 'wb') as f:
#         pickle.dump(encodings, f)

#     attendances = Attendance.objects.filter(student=student, face_updated=False)
#     for attendance in attendances:
#         attendance.face_updated = True
#         attendance.failed_face_attempts = 0
#         attendance.save()

#     return JsonResponse({'status': 'success', 'message': 'Face registered successfully'})

# @csrf_exempt
# def verify_face_api(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Only POST allowed'}, status=405)

#     try:
#         student = get_authenticated_student(request)
#         student_id = student.id
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=401)

#     lecture_id = request.POST.get('lecture_id')
#     if not lecture_id:
#         return JsonResponse({'error': 'lecture_id is required'}, status=400)

#     try:
#         lecture = LectureSession.objects.get(id=lecture_id)
#     except LectureSession.DoesNotExist:
#         return JsonResponse({'error': 'Lecture not found.'}, status=404)

#     # ✅ Check active QR
#     qr_session_exists = QRCodeSession.objects.filter(
#         lecture=lecture,
#         is_active=True,
#         created_at__gte=timezone.now() - timedelta(minutes=15)
#     ).exists()

#     if not qr_session_exists:
#         return JsonResponse({'error': 'Attendance for this lecture is currently closed (no active QR).'}, status=403)

#     if not check_student_enrollment(student, lecture):
#         return JsonResponse({'error': 'You are not enrolled in this course. Cannot mark attendance.'}, status=403)

#     image = request.FILES.get('image')
#     if image is None:
#         return JsonResponse({'error': 'image is required'}, status=400)

#     input_encoding = get_face_encoding_from_image_file(image)
#     if input_encoding is None:
#         return JsonResponse({'error': 'No face detected in the provided image'}, status=400)

#     file_path = os.path.join(DATA_FOLDER, f"{student_id}.pkl")
#     if not os.path.exists(file_path):
#         return JsonResponse({'error': 'No face data registered. Please register your face first.'}, status=400)

#     with open(file_path, 'rb') as f:
#         known_encodings = pickle.load(f)

#     matches = face_recognition.compare_faces(known_encodings, input_encoding)
#     if not any(matches):
#         attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
#         attendance.failed_face_attempts += 1
#         attendance.save()
#         return JsonResponse({'error': 'Face verification failed'}, status=403)

#     attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
#     attendance.status = 'Present'
#     attendance.face_updated = True
#     attendance.failed_face_attempts = 0
#     attendance.save()

#     return JsonResponse({'status': 'success', 'message': 'Face verification successful. Attendance marked as present.'})
#############################################################################################




import random
import os
import qrcode
import json
import pickle
import numpy as np
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from io import BytesIO
from PIL import Image
import face_recognition
from accounts.models import Doctor, Student  # استورد موديل الدكتور الصحيح
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework_simplejwt.authentication import JWTAuthentication

from courses.models import Course, StudentCourse
from schedule.models import Schedule
from attendance.models import Attendance
from .models import QRCodeSession, LectureSession

jwt_authenticator = JWTAuthentication()

#########################
# Helper Functions
#########################

def check_student_enrollment(student, lecture):
    """تحقق إذا كان الطالب مسجل في المادة الخاصة بالمحاضرة"""
    course = lecture.course
    return StudentCourse.objects.filter(student=student, course=course).exists()

def get_authenticated_student(request):
    """استخرج الطالب من التوكن"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Exception('Authorization header missing or invalid')

    token = auth_header.split(' ')[1]
    validated_token = jwt_authenticator.get_validated_token(token)
    user = jwt_authenticator.get_user(validated_token)

    if not hasattr(user, 'student'):
        raise Exception('Only students can perform this action')

    return user.student

def get_face_encoding_from_image_file(image_file):
    """استخراج face encoding من صورة"""
    img = Image.open(image_file)
    img = img.convert('RGB')
    img_array = np.array(img)
    face_locations = face_recognition.face_locations(img_array)
    if not face_locations:
        return None
    encoding = face_recognition.face_encodings(img_array, face_locations)[0]
    return encoding

#########################
# API Endpoints
#########################
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime
from .models import LectureSession
from courses.models import Course
from accounts.models import Doctor
from rest_framework_simplejwt.authentication import JWTAuthentication

jwt_authenticator = JWTAuthentication()

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime
from courses.models import Course
from attendance.models import LectureSession
from accounts.models import Doctor
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from accounts.models import Doctor
from courses.models import Course
from attendance.models import LectureSession
import os
import json
import random
import threading
import time
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from .models import Course, LectureSession, QRCodeSession
import qrcode

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('create_lecture')  # غيّري لو عندك صفحة تانية بعد اللوج إن
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_lecture_api(request):
    try:
        # جبنا الدكتور من الـ request.user
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response({'error': 'Only doctors can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)

        # ------ GET: رجّع المواد المرتبطة بالدكتور ------
        if request.method == 'GET':
            courses = Course.objects.filter(doctor=doctor)
            courses_data = [
                {
                    'id': course.id,
                    'name': course.name,
                    'department': course.structure.department,
                    'year': course.structure.year,
                    'semester': course.structure.semester
                }
                for course in courses
            ]
            return Response({'status': 'success', 'courses': courses_data}, status=status.HTTP_200_OK)

        # ------ POST: أنشئ محاضرة ------
        data = request.data
        course_name = data.get('course_name')
        lecture_date_str = data.get('lecture_date')
        lecture_name = data.get('lecture_name')
        department = data.get('department')

        if not all([course_name, lecture_date_str, lecture_name, department]):
            return Response({'error': 'Missing required fields: course_name, lecture_date, lecture_name, department'}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.filter(
            name=course_name,
            doctor=doctor,
            structure__department=department
        ).first()

        if not course:
            return Response({'error': 'Course not found or you are not the assigned doctor for this department'}, status=status.HTTP_404_NOT_FOUND)

        lecture_date = datetime.strptime(lecture_date_str, '%Y-%m-%d').date()

        lecture = LectureSession.objects.create(
            course=course,
            date=lecture_date,
            title=lecture_name,
            is_open_for_attendance=False
        )

        return Response({'status': 'success', 'lecture_id': lecture.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#--------------------------------------------------------------------------------------------
# # views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import Doctor
from courses.models import Course
from .models import LectureSession
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def create_lecture_view(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
        print("✅ Doctor found:", doctor)
    except Doctor.DoesNotExist:
        print("❌ Doctor not found for user:", request.user)
        messages.error(request, "You must be a doctor to access this page.")
        return redirect('home')

    courses = doctor.courses.all()
    print("📚 Courses found:", courses)

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        lecture_name = request.POST.get('lecture_name')
        lecture_date = request.POST.get('lecture_date')

        if not all([course_id, lecture_name, lecture_date]):
            messages.error(request, "All fields are required.")
        else:
            course = Course.objects.filter(id=course_id, doctor=doctor).first()
            if not course:
                messages.error(request, "Course not found or not assigned to you.")
            else:
                lecture = LectureSession.objects.create(
                    course=course,
                    title=lecture_name,
                    date=datetime.strptime(lecture_date, "%Y-%m-%d").date(),
                    is_open_for_attendance=False
                )
                messages.success(request, f"Lecture '{lecture.title}' created successfully.")

                return redirect('create_lecture')

    return render(request, 'attendance/create_lecture.html', {'courses': courses})


#################
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Course, LectureSession, QRCodeSession
from django.utils import timezone
import threading, os, random, json, time
from datetime import datetime
import qrcode
from django.conf import settings

def rotate_qr_code(lecture, course):
    """تحديث رمز QR كل دقيقة لمدة 15 دقيقة"""
    for _ in range(15):
        # حذف الأكواد القديمة
        QRCodeSession.objects.filter(
            lecture=lecture,
            created_at__lt=timezone.now() - timezone.timedelta(seconds=60)
        ).delete()

        # إنشاء كود جديد
        new_code = str(random.randint(1000, 9999))
        qr_data = {
            'course_name': course.name,
            'lecture_date': lecture.date.strftime('%Y-%m-%d'),
            'code': new_code,
        }
        qr_code_data = json.dumps(qr_data)

        qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(qr_codes_dir, exist_ok=True)
        filename = f"qr_code_{int(datetime.now().timestamp())}.png"
        file_path = os.path.join(qr_codes_dir, filename)

        qr = qrcode.make(qr_code_data)
        qr.save(file_path)

        QRCodeSession.objects.create(
            lecture=lecture,
            code=new_code,
            image=f'qr_codes/{filename}',
            is_active=True
        )

        time.sleep(60)

    lecture.is_open_for_attendance = False
    lecture.save()

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
import threading, time, os, json, random
import qrcode
from .models import LectureSession, Course, QRCodeSession

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import LectureSession, QRCodeSession, Course  # حسب ما عندك
import threading

from datetime import timedelta

@login_required
def start_qr_session_page(request):
    if request.method == "POST":
        lecture_id = request.POST.get("lecture_id")
        lecture = get_object_or_404(LectureSession, id=lecture_id)
        course = lecture.course

        now = timezone.now()
        session_started = lecture.qr_session_started_at

        # 🛑 تحقق إذا الجلسة بدأت بالفعل ومعدتش 15 دقيقة
        if session_started and (now - session_started < timedelta(minutes=15)):
            return JsonResponse({'error': 'QR session already started and still active for this lecture.'}, status=400)

        # ✅ ابدأ جلسة جديدة
        lecture.is_open_for_attendance = True
        lecture.qr_session_started_at = now
        lecture.save()

        threading.Thread(target=rotate_qr_code, args=(lecture, course), daemon=True).start()
        return JsonResponse({'status': 'QR session started.'})

    # GET: رجع المحاضرات اللي ممكن تبدأ لها QR
    try:
        doctor = request.user.doctor
    except:
        return JsonResponse({'error': 'You are not assigned as a doctor.'}, status=403)

    # 🎯 فلترة المحاضرات اللي مفيهاش QR بدأ قريب
    now = timezone.now()
    lectures = LectureSession.objects.filter(
        is_open_for_attendance=False,
        course__doctor=doctor
    ).exclude(
        qr_session_started_at__gte=now - timedelta(minutes=15)
    )

    return render(request, "qr/start_qr_session.html", {"lectures": lectures})




@login_required
def get_latest_qr(request, lecture_id):
    qr = QRCodeSession.objects.filter(lecture_id=lecture_id).order_by('-created_at').first()
    if not qr:
        return JsonResponse({'image_url': None})
    return JsonResponse({'image_url': qr.image.url})


def rotate_qr_code(lecture, course):
    """تحديث رمز QR كل دقيقة لمدة 15 دقيقة"""

    for _ in range(15):
        # حذف الأكواد القديمة
        expired_qrs = QRCodeSession.objects.filter(
            lecture=lecture,
            created_at__lt=timezone.now() - timezone.timedelta(seconds=60)
        )
        for qr in expired_qrs:
            if qr.image and os.path.exists(qr.image.path):
                os.remove(qr.image.path)
            qr.delete()

        # إنشاء كود جديد
        new_code = str(random.randint(1000, 9999))
        qr_data = {
            'course_name': course.name,
            'lecture_date': lecture.date.strftime('%Y-%m-%d'),
            'code': new_code,
        }
        qr_code_data = json.dumps(qr_data)

        # حفظ صورة QR جديدة
        qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(qr_codes_dir, exist_ok=True)

        filename = f"qr_code_{int(time.time())}.png"
        file_path = os.path.join(qr_codes_dir, filename)

        qr = qrcode.make(qr_code_data)
        qr.save(file_path)

        # حفظ الجلسة
        QRCodeSession.objects.create(
            lecture=lecture,
            code=new_code,
            image=f'qr_codes/{filename}',
            is_active=True
        )

        time.sleep(60)

    lecture.is_open_for_attendance = False
    lecture.save()



#############

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from attendance.models import LectureSession, Attendance
from courses.models import Course, StudentCourse

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from datetime import datetime

@login_required
def doctor_attendance_table(request):
    try:
        doctor = request.user.doctor
    except:
        return render(request, "error.html", {"message": "You are not assigned as a doctor."})

    if request.method == "POST":
        # 1. تحديث حضور الطلاب
        for key, value in request.POST.items():
            if key.startswith("attendance_"):
                parts = key.split("_")
                if len(parts) == 3:
                    _, student_id, lecture_id = parts
                    if student_id.isdigit() and lecture_id.isdigit():
                        status = value

                        student = Student.objects.filter(id=int(student_id)).first()
                        lecture = LectureSession.objects.filter(id=int(lecture_id)).first()
                        if student and lecture:
                            attendance_obj, created = Attendance.objects.get_or_create(
                                student=student,
                                lecture=lecture,
                                defaults={"status": status}
                            )
                            if not created and attendance_obj.status != status:
                                attendance_obj.status = status
                                attendance_obj.save()

            if key.startswith("lecture_date_"):
                lecture_id = key.replace("lecture_date_", "")
                if lecture_id.isdigit():
                    lecture = LectureSession.objects.filter(id=int(lecture_id)).first()
                    if lecture:
                        try:
                            new_date = parse_date(value)
                            if new_date and lecture.date != new_date:
                                lecture.date = new_date
                                lecture.save()
                        except:
                            pass

            if key.startswith("lecture_title_"):
                lecture_id = key.replace("lecture_title_", "")
                if lecture_id.isdigit():
                    lecture = LectureSession.objects.filter(id=int(lecture_id)).first()
                    if lecture:
                        new_title = value.strip()
                        if lecture.title != new_title and new_title:
                            lecture.title = new_title
                            lecture.save()

        # بعد الحفظ، إعادة التوجيه لتفادي POST متكرر
        return redirect("doctor_attendance_table")

    # إذا كان GET أو غيره: جلب البيانات للعرض
    courses = Course.objects.filter(doctor=doctor)
    result = []

    for course in courses:
        lectures = LectureSession.objects.filter(course=course).order_by('date')
        students = StudentCourse.objects.filter(course=course).select_related("student")

        lecture_headers = [{"title": lec.title, "date": lec.date, "id": lec.id} for lec in lectures]

        student_rows = []
        for sc in students:
            attendance_pairs = []
            for lec in lectures:
                att = Attendance.objects.filter(student=sc.student, lecture=lec).first()
                status = att.status if att else "absent"
                attendance_pairs.append((lec, status))
            student_rows.append({
                "student_name": sc.student.name,
                "student_id": sc.student.id,
                "attendance_pairs": attendance_pairs
            })

        result.append({
            "course_name": course.name,
            "structure": str(course.structure),
            "lectures": lecture_headers,
            "students": student_rows
        })

    return render(request, "attendance/doctor_attendance_table.html", {"data": result})

############

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def student_open_lectures_page(request):
    return render(request, 'open_lectures.html')

#--------------------------------------------------------------------------------------------

def rotate_qr_code(lecture, course):
    """تحديث رمز QR كل دقيقة لمدة 15 دقيقة"""

    for _ in range(15):
        # حذف الأكواد القديمة
        expired_qrs = QRCodeSession.objects.filter(
            lecture=lecture,
            created_at__lt=timezone.now() - timezone.timedelta(seconds=60)
        )

        for qr in expired_qrs:
            # حذف الصورة من الميديا
            if qr.image and os.path.exists(qr.image.path):
                os.remove(qr.image.path)
            qr.delete()

        # إنشاء كود جديد
        new_code = str(random.randint(1000, 9999))
        qr_data = {
            'course_name': course.name,
            'lecture_date': lecture.date.strftime('%Y-%m-%d'),
            'code': new_code,
        }
        qr_code_data = json.dumps(qr_data)

        # حفظ صورة QR جديدة
        qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(qr_codes_dir, exist_ok=True)

        filename = f"qr_code_{int(datetime.now().timestamp())}.png"
        file_path = os.path.join(qr_codes_dir, filename)

        qr = qrcode.make(qr_code_data)
        qr.save(file_path)

        # إنشاء QRCodeSession جديد
        QRCodeSession.objects.create(
            lecture=lecture,
            code=new_code,
            image=f'qr_codes/{filename}',
            is_active=True
        )

        time.sleep(60)

    # بعد 15 دقيقة، نغلق الحضور
    lecture.is_open_for_attendance = False
    lecture.save()


def generate_qr_code_ajax(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)

    lecture_id = request.GET.get('lecture_id')
    lecture = LectureSession.objects.filter(id=lecture_id).first() if lecture_id else None

    if not lecture:
        return JsonResponse({'error': 'Lecture not found'}, status=404)

    # فتح المحاضرة للحضور
    lecture.is_open_for_attendance = True
    lecture.save()

    # بدء التحديث المستمر للـ QR
    threading.Thread(target=rotate_qr_code, args=(lecture, course), daemon=True).start()

    return JsonResponse({'status': 'QR session started'})


from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import QRCodeSession
from courses.models import StudentCourse
from accounts.models import Student  # حسب مكان موديل الطالب


from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from attendance.models import QRCodeSession
from courses.models import StudentCourse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from django.utils.timezone import localtime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_open_lectures_for_student(request):
    try:
        student = request.user.student

        enrolled_courses_ids = StudentCourse.objects.filter(
            student=student
        ).values_list('course_id', flat=True)

        fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)

        active_qr_sessions = QRCodeSession.objects.filter(
            is_active=True,
            created_at__gte=fifteen_minutes_ago,
            lecture__course_id__in=enrolled_courses_ids
        ).select_related('lecture', 'lecture__course')

        open_lectures = []
        for session in active_qr_sessions:
            lecture = session.lecture
            course = lecture.course

            # تحديد اليوم الحالي (مثلاً 'Monday')
            today_weekday = localtime().strftime('%A')

            # جلب الجدول المرتبط بالمادة واليوم الحالي
            schedule = Schedule.objects.filter(
                course=course,
                day=today_weekday,
                student_structure__student=student
            ).first()

            open_lectures.append({
                'lecture_id': lecture.id,
                'lecture_date': lecture.date.strftime("%Y-%m-%d"),
                'course_name': course.name,
                'room': schedule.room if schedule else "",
                'start_time': schedule.start_time.strftime("%H:%M") if schedule and schedule.start_time else "",
                'end_time': schedule.end_time.strftime("%H:%M") if schedule and schedule.end_time else "",
            })

        return Response({
            'status': 'success',
            'open_lectures': open_lectures
        })

    except Exception as e:
        print(f"❌ حصل خطأ: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)




def verify_qr_code(request):
    """التحقق من صحة رمز QR"""
    code = request.GET.get('qr_code_data')
    try:
        if not code or not code.isdigit():
            return JsonResponse({'status': 'error', 'message': 'Invalid QR Code (not numeric)'})

        qr_session = QRCodeSession.objects.get(
            code=int(code),
            is_active=True,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        )

        return JsonResponse({
            'status': 'success',
            'message': 'QR Code is valid',
            'course_name': qr_session.course.name,
            'lecture_date': qr_session.lecture.date.strftime("%Y-%m-%d") if qr_session.lecture else None,
            'lecture_id': qr_session.lecture.id if qr_session.lecture else None,
        })

    except QRCodeSession.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid QR Code'})

#########################
# Location Verification
#########################

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import date
from schedule.models import Schedule
import json

BUILDING_ZONES = {
    'A': [(30.1000, 31.2980), (30.1000, 31.2990), (30.1010, 31.2990), (30.1010, 31.2980)],
    'G': [(30.1020, 31.2950), (30.1020, 31.2960), (30.1030, 31.2960), (30.1030, 31.2950)],
    'C': [(30.1040, 31.2970), (30.1040, 31.2980), (30.1050, 31.2980), (30.1050, 31.2970)],
    'D': [(30.1060, 31.2990), (30.1060, 31.3000), (30.1070, 31.3000), (30.1070, 31.2990)],
    'F': [(30.1080, 31.3010), (30.1080, 31.3020), (30.1090, 31.3020), (30.1090, 31.3010)],
}

def is_point_in_polygon(lat, lon, polygon):
    x = lon
    y = lat
    inside = False
    n = len(polygon)
    p1x, p1y = polygon[0][1], polygon[0][0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n][1], polygon[i % n][0]
        if min(p1y, p2y) < y <= max(p1y, p2y):
            if x <= max(p1x, p2x):
                xinters = (y - p1y) * (p2x - p1x) / ((p2y - p1y) + 1e-10) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y
    return inside


@csrf_exempt
def verify_location(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        course_id = data.get('course_id')  # ID الكورس اللي عايز يتسجل حضوره
        student_structure_id = data.get('student_structure_id')  # جدول الطالب

        if not all([lat, lon, course_id, student_structure_id]):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        # نحدد اليوم الحالي (مثلاً: "Monday")
        day_name = date.today().strftime('%A')

        # نجيب أقرب محاضرة (Lecture فقط) للطالب في اليوم الحالي
        lecture = Schedule.objects.filter(
            student_structure_id=student_structure_id,
            course_id=course_id,
            day=day_name,
            type='Lecture'
        ).order_by('slot_number').first()

        if not lecture:
            return JsonResponse({'error': 'No lecture found for today for this course'}, status=404)

        building_code = lecture.room[0].upper()  # أول حرف من اسم القاعة

        if building_code not in BUILDING_ZONES:
            return JsonResponse({'error': f'Unknown building zone for room {lecture.room}'}, status=400)

        polygon = BUILDING_ZONES[building_code]
        inside = is_point_in_polygon(lat, lon, polygon)

        return JsonResponse({
            'status': 'success',
            'inside': inside,
            'room': lecture.room,
            'building': building_code,
            'course': str(lecture.course),
            'message': f"User is {'inside' if inside else 'outside'} building {building_code}"
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


#########################
# Face Recognition APIs
#########################

DATA_FOLDER = os.path.join(settings.BASE_DIR, 'students_data')
os.makedirs(DATA_FOLDER, exist_ok=True)

@csrf_exempt
def register_face_api(request):
    """تسجيل الوجه للطالب (3 صور)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        student = get_authenticated_student(request)
        student_id = student.id
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=401)

    images = [request.FILES.get(f'image{i}') for i in range(1, 4)]
    if any(img is None for img in images):
        return JsonResponse({'error': 'Three images (image1, image2, image3) are required'}, status=400)

    encodings = []
    for img in images:
        encoding = get_face_encoding_from_image_file(img)
        if encoding is None:
            return JsonResponse({'error': 'No face detected in one of the images'}, status=400)
        encodings.append(encoding)

    file_path = os.path.join(DATA_FOLDER, f"{student_id}.pkl")
    with open(file_path, 'wb') as f:
        pickle.dump(encodings, f)

    # تحديث الحضور السابق الذي لم يتم تحديث الوجه فيه
    attendances = Attendance.objects.filter(student=student, face_updated=False)
    for attendance in attendances:
        attendance.face_updated = True
        attendance.failed_face_attempts = 0
        attendance.save()

    return JsonResponse({'status': 'success', 'message': 'Face registered successfully'})

@csrf_exempt
def verify_face_api(request):
    """التحقق من الوجه وإعتماد الحضور"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        student = get_authenticated_student(request)
        student_id = student.id
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=401)

    lecture_id = request.POST.get('lecture_id')
    if not lecture_id:
        return JsonResponse({'error': 'lecture_id is required'}, status=400)

    try:
        lecture = LectureSession.objects.get(id=lecture_id)
    except LectureSession.DoesNotExist:
        return JsonResponse({'error': 'Lecture not found.'}, status=404)

    # تحقق من وجود رمز QR فعال
    qr_session_exists = QRCodeSession.objects.filter(
        lecture=lecture,
        is_active=True,
        created_at__gte=timezone.now() - timedelta(minutes=15)
    ).exists()

    if not qr_session_exists:
        return JsonResponse({'error': 'Attendance for this lecture is currently closed (no active QR).'}, status=403)

    if not check_student_enrollment(student, lecture):
        return JsonResponse({'error': 'You are not enrolled in this course. Cannot mark attendance.'}, status=403)

    image = request.FILES.get('image')
    if image is None:
        return JsonResponse({'error': 'image is required'}, status=400)

    input_encoding = get_face_encoding_from_image_file(image)
    if input_encoding is None:
        return JsonResponse({'error': 'No face detected in the provided image'}, status=400)

    file_path = os.path.join(DATA_FOLDER, f"{student_id}.pkl")
    if not os.path.exists(file_path):
        return JsonResponse({'error': 'No face data registered. Please register your face first.'}, status=400)

    with open(file_path, 'rb') as f:
        known_encodings = pickle.load(f)

    matches = face_recognition.compare_faces(known_encodings, input_encoding)
    if not any(matches):
        attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
        attendance.failed_face_attempts += 1
        if attendance.failed_face_attempts >= 3:
            attendance.face_updated = False
        attendance.save()
        return JsonResponse({'error': 'Face does not match registered data. Please try again.'}, status=401)

    # تسجيل الحضور
    attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
    attendance.is_present = True
    attendance.face_updated = True
    attendance.failed_face_attempts = 0
    attendance.save()

    return JsonResponse({'status': 'success', 'message': 'Attendance marked successfully.'})


# students/views.py أو ملف views المناسب
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from courses.models import StudentCourse
from .models import Attendance, LectureSession
from courses.models import Course
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_summary(request):
    user = request.user

    # نتأكد إنه طالب
    if not hasattr(user, 'student'):
        return Response({"detail": "User is not a student."}, status=403)

    student = user.student
    student_courses = StudentCourse.objects.filter(student=student)

    data = []
    for enrollment in student_courses:
        course = enrollment.course
        lectures = LectureSession.objects.filter(course=course)
        total_lectures = lectures.count()
        
        attended_count = Attendance.objects.filter(
            student=student,
            lecture__in=lectures,
            status='present'
        ).count()

        percentage = (
            (attended_count / total_lectures) * 100 if total_lectures > 0 else 0
        )
        status = "regular" if percentage >= 75 else "at risk"

        data.append({
            "course": course.name,
            "department": course.structure.get_department_display() if course.structure else "",
            "year": course.structure.get_year_display() if course.structure else "",
            "semester": course.structure.get_semester_display() if course.structure else "",
            "attended_lectures": attended_count,
            "total_lectures": total_lectures,
            "percentage": round(percentage, 2),
            "status": status
        })


    return Response(data)



from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from attendance.models import LectureSession, Attendance
from courses.models import Course, StudentCourse
from accounts.models import Doctor
from django.shortcuts import get_object_or_404

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctor_attendance_overview(request):
    # 🧑‍⚕️ تأكد إن اليوزر دكتور
    try:
        doctor = request.user.doctor
    except:
        return Response({"error": "You are not assigned as a doctor."}, status=403)

    # 📚 رجع كل المواد المرتبطة بالدكتور
    courses = Course.objects.filter(doctor=doctor)

    result = []

    for course in courses:
        course_data = {
            "course_id": course.id,
            "course_name": course.name,
            "structure": str(course.structure),
            "lectures": []
        }

        lectures = LectureSession.objects.filter(course=course).order_by('date')

        for lecture in lectures:
            lecture_data = {
                "lecture_id": lecture.id,
                "lecture_title": lecture.title,
                "date": lecture.date,
                "students": []
            }

            # كل الطلبة في الكورس ده
            student_courses = StudentCourse.objects.filter(course=course).select_related("student")

            for sc in student_courses:
                attendance = Attendance.objects.filter(student=sc.student, lecture=lecture).first()
                lecture_data["students"].append({
                    "student_id": sc.student.id,
                    "student_name": sc.student.name,
                    "status": attendance.status if attendance else "absent"
                })

            course_data["lectures"].append(lecture_data)

        result.append(course_data)

    return Response(result)
