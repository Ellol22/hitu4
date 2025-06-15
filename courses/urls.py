from django.urls import path
from .views import DepartmentCoursesView

urlpatterns = [
    path('my-department-courses/', DepartmentCoursesView.as_view(), name='department-courses'),
]
