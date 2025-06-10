from django.urls import path
from . import views

urlpatterns = [
    # دكتور: إنشاء محاضرة جديدة
    path('create_lecture/', views.create_lecture_api, name='create_lecture_api'),

    # دكتور: توليد رمز QR للمحاضرة (AJAX)
    path('generate_qr/<str:course_name>/', views.generate_qr_code_ajax, name='generate_qr_ajax'),

    # طالب: جلب المحاضرات المفتوحة برمز QR فعال
    path('open_lectures/', views.get_open_lectures_for_student, name='get_open_lectures_for_student'),

    # طالب: التحقق من صحة رمز QR
    path('verify_qr/', views.verify_qr_code, name='verify_qr'),

    # طالب: التحقق من الموقع الجغرافي (مباني الجامعة)
    path('verify_location/', views.verify_location, name='verify_location'),

    # طالب: تسجيل الوجه (3 صور)
    path('register_face/', views.register_face_api, name='register_face_api'),

    # طالب: التحقق من الوجه وتسجيل الحضور
    path('verify_face/', views.verify_face_api, name='verify_face_api'),

    # الطالب يشوف حضورة قد اي
    path("student/", views.student_attendance_summary , name="student_attendance_summary")
]