from django.urls import path
from . import views
from .views import login_view 

urlpatterns = [
    # دكتور: إنشاء محاضرة جديدة
    path('create_lecture/', views.create_lecture_api, name='create_lecture_api'),
    path('login/', login_view, name='login'),  
    path('doctor/create-lecture/', views.create_lecture_view, name='create_lecture'), #Html
    path('qr/start/', views.start_qr_session_page, name='start_qr_page'),#Html
    path('qr/latest/<int:lecture_id>/', views.get_latest_qr, name='get_latest_qr'),#Html
    path('doctor/attendance-table/', views.doctor_attendance_table, name='doctor_attendance_table'),
    path('student/open-lectures/', views.student_open_lectures_page, name='student_open_lectures'),




    # دكتور: توليد رمز QR للمحاضرة (AJAX)
    path('generate_qr/<int:course_id>/', views.generate_qr_code_ajax, name='generate_qr_ajax'),

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
    path("student/", views.student_attendance_summary , name="student_attendance_summary"),

    # فنكشن بترجع كشف كامل للطلبة و كل طالب قدامه حضورة و غيابة 
    path("doctor/", views.doctor_attendance_overview, name="doctor_attendance_overview"),

]