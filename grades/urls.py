from django.urls import path
from grades import views

urlpatterns = [
    path('student/', views.my_grades, name='my_grades'),
    path('doctor_courses/', views.doctor_courses, name='doctor_courses'),
    path('doctor/<str:course_name>/', views.manage_course_grades, name='doctor_grades'),
]