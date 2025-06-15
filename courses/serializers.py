from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'structure']


# في courses/serializers.py

from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'doctor_name']
