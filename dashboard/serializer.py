from rest_framework import serializers
from accounts.models import Doctor, Student
from django.contrib.auth.models import User

from courses.models import Course
from .models import Announcement

class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    structure = serializers.PrimaryKeyRelatedField(read_only=True)  # عشان يرجع ID مش object كامل
    image = serializers.SerializerMethodField()  # هنجيب الصورة يدويًا

    class Meta:
        model = Student
        fields = ['username', 'first_name', 'email', 'name', 'mobile', 'national_id', 'structure', 'image']

    def get_image(self, obj):
        try:
            return obj.dash.image.url if obj.dash and obj.dash.image else None
        except:
            return None

class DoctorSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    departments = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['name', 'national_id', 'mobile', 'image', 'structures', 'email', 'courses' , 'departments']

    def get_courses(self, obj):
        return [course.name for course in obj.courses.all()]  # أو أي تمثيل للكورسات

    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        try:
            return obj.dash.image.url if obj.dash and obj.dash.image else None
        except:
            return None


    def get_departments(self, obj):
        return list(set([
            structure.department.name  # أو structure.department لو عايزة ID
            for structure in obj.structures.all()
            if structure.department
        ]))



############################################################################


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']