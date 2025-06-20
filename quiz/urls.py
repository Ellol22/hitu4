from django.urls import path
from .views import (
    staff_courses, staff_quizzes, staff_quiz_detail,
    staff_assignments, staff_assignment_detail,
    student_courses, student_quiz_detail,student_quizzes,
    student_assignments,student_submit_assignment,student_delete_submission,
)


urlpatterns = [
    path('staff/courses/', staff_courses, name='staff-courses'),
    path('staff/quizzes/', staff_quizzes, name='staff-quizzes'),
    path('staff/quizzes/<int:quiz_id>/', staff_quiz_detail, name='staff-quiz-detail'),
    path('staff/assignments/', staff_assignments, name='staff-assignments'),
    path('staff/assignments/<int:assignment_id>/', staff_assignment_detail, name='staff-assignment-detail'),
    # path('staff/quizzes/notify/', staff_quizzes_notify, name='staff-quizzes-notify'),

    ######-----------------------------------

    path('student/courses/', student_courses, name='student-courses'),
    path('student/quizzes/', student_quizzes, name='student-quizzes'),
    path('student/quizzes/<int:quiz_id>/', student_quiz_detail, name='student-submit-quiz'),
    path('student/assignments/', student_assignments, name='student-assignments'),
    path('student/assignments/<int:assignment_id>/submit/', student_submit_assignment, name='student-submit-assignment'),
    path('student/submissions/<int:submission_id>/delete/', student_delete_submission, name='student-delete-submission'),
]