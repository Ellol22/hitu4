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
from accounts.models import Doctor  # استورد موديل الدكتور الصحيح
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

@csrf_exempt
def create_lecture_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Exception('Authorization header missing or invalid')

        token = auth_header.split(' ')[1]
        validated_token = jwt_authenticator.get_validated_token(token)
        user = jwt_authenticator.get_user(validated_token)

        try:
            doctor = Doctor.objects.get(user=user)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Only doctors can create lectures.'}, status=403)

        data = json.loads(request.body)
        course_name = data.get('course_name')
        lecture_date_str = data.get('lecture_date')
        lecture_name = data.get('lecture_name')
        department = data.get('department')

        if not all([course_name, lecture_date_str, lecture_name, department]):
            return JsonResponse({'error': 'Missing required fields: course_name, lecture_date, lecture_name, department'}, status=400)

        # جيب الكورس بناءً على department الموجود في structure
        course = Course.objects.filter(
            name=course_name,
            doctor=doctor,
            structure__department=department
        ).first()

        if not course:
            return JsonResponse({'error': 'Course not found or you are not the assigned doctor for this department'}, status=404)

        lecture_date = datetime.strptime(lecture_date_str, '%Y-%m-%d').date()

        lecture = LectureSession.objects.create(
            course=course,
            date=lecture_date,
            title=lecture_name,
            is_open_for_attendance=False
        )

        return JsonResponse({'status': 'success', 'lecture_id': lecture.id})

    except Exception as e:
        return JsonResponse({'error': str(e)})


def generate_qr_code_ajax(request, course_id):
    """توليد رمز QR للمحاضرة"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)

    lecture_id = request.GET.get('lecture_id')
    lecture = None
    if lecture_id:
        lecture = LectureSession.objects.filter(id=lecture_id).first()

    random_number = random.randint(1000, 9999)

    qr_data = {
        'course_name': course.name,
        'lecture_date': lecture.date.strftime('%Y-%m-%d') if lecture else '',
        'code': random_number,
    }
    qr_code_data = json.dumps(qr_data)

    qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
    os.makedirs(qr_codes_dir, exist_ok=True)

    filename = f"qr_code_{int(datetime.now().timestamp())}.png"
    file_path = os.path.join(qr_codes_dir, filename)

    qr = qrcode.make(qr_code_data)
    qr.save(file_path)

    qr_session = QRCodeSession.objects.create(
        course=course,
        lecture=lecture,
        code=str(random_number),
        image=f'qr_codes/{filename}',
        is_active=True
    )

    # فتح المحاضرة للحضور
    if lecture:
        lecture.is_open_for_attendance = True
        lecture.save()

    image_url = f"{settings.MEDIA_URL}qr_codes/{filename}"
    return JsonResponse({'image_url': image_url})

def get_open_lectures_for_student(request):
    """إرجاع المحاضرات المفتوحة التي لها رمز QR فعال للطالب"""
    try:
        student = get_authenticated_student(request)
        enrolled_courses = StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)

        active_qr_sessions = QRCodeSession.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timedelta(minutes=15),
            course_id__in=enrolled_courses
        ).select_related('lecture')

        open_lectures = []
        for qr_session in active_qr_sessions:
            lecture = qr_session.lecture
            if lecture:
                open_lectures.append({
                    'lecture_id': lecture.id,
                    'lecture_date': lecture.date.strftime("%Y-%m-%d"),
                    'course_name': qr_session.course.name,
                    'qr_image_url': f"{settings.MEDIA_URL}{qr_session.image}",
                })

        return JsonResponse({'status': 'success', 'open_lectures': open_lectures})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

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
        building = data.get('building')  # اسم المبنى المطلوب التحقق منه

        if not building or building not in BUILDING_ZONES:
            return JsonResponse({'error': 'Invalid or missing building parameter'}, status=400)

        polygon = BUILDING_ZONES[building]
        inside = is_point_in_polygon(lat, lon, polygon)

        if inside:
            return JsonResponse({'status': 'success', 'message': f'User is inside building {building}', 'inside': True})
        else:
            return JsonResponse({'status': 'success', 'message': f'User is outside building {building}', 'inside': False})

    except (ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request data'}, status=400)
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
