from django.urls import path
from .views import (
    task_list_create,
    task_detail,
    submission_create,
    submission_detail,
    doctor_courses
)

urlpatterns = [
    # ---------- TASKS ----------
    path('', task_list_create, name='task-list-create'),        # GET + POST
    path('tasks/<int:pk>/', task_detail, name='task-detail'),         # GET + PUT + DELETE (Doctor only)
    path('my_courses/', doctor_courses, name='doctor-courses'),       # GET Doctor courses

    # ---------- SUBMISSIONS ----------
    path('submissions/create/', submission_create, name='submission-create'),   # POST (Student only)
    path('submissions/<int:pk>/', submission_detail, name='submission-detail'), # GET + PUT + DELETE (Student only)
]
