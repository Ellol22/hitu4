from django.urls import path
from .views import personal_info ,announcement_api

urlpatterns = [
    path('pers-info/', personal_info, name='pers-info'),
    path('announcements', announcement_api ,name='announcements/'),
]