from django.urls import path
from .views import (
    task_list_create,
    task_detail,
    submission_create,
    submission_detail,
)

urlpatterns = [
    # ---------- TASKS ----------
    path('tasks/', task_list_create, name='task-list-create'),        # GET + POST
    path('tasks/<int:pk>/', task_detail, name='task-detail'),         # GET + PUT + DELETE (Doctor only)

    # ---------- SUBMISSIONS ----------
    path('submissions/create/', submission_create, name='submission-create'),   # POST (Student only)
    path('submissions/<int:pk>/', submission_detail, name='submission-detail'), # GET + PUT + DELETE (Student only)
]
