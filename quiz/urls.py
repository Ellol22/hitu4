from django.urls import path
from .views import (
    staff_courses, staff_quizzes, staff_quiz_detail,
    staff_assignments, staff_assignment_detail, staff_quizzes_notify
)

urlpatterns = [
    path('staff/courses/', staff_courses, name='staff-courses'),
    path('staff/quizzes/', staff_quizzes, name='staff-quizzes'),
    path('staff/quizzes/<int:quiz_id>/', staff_quiz_detail, name='staff-quiz-detail'),
    path('staff/assignments/', staff_assignments, name='staff-assignments'),
    path('staff/assignments/<int:assignment_id>/', staff_assignment_detail, name='staff-assignment-detail'),
    path('staff/quizzes/notify/', staff_quizzes_notify, name='staff-quizzes-notify'),
]