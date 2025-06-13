from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Student, Doctor

# Serializer لليوزر الأساسي (اللي بيحتوي على اليوزرنيم، الإيميل، والاسم الكامل)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name']

# Serializer للطالب مع دعم إنشاء وتحديث البيانات المرتبطة باليوزر
class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # بيانات اليوزر للقراءة فقط

    class Meta:
        model = Student
        fields = ['id', 'user', 'name', 'mobile', 'national_id', 'sec_num']  # تأكد من وجود sec_num في الموديل

# Serializer للدكتور مع دعم بيانات اليوزر
class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'name', 'mobile', 'national_id', 'role']  # تأكد من وجود role في الموديل

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # You can add custom claims here if needed
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        if hasattr(user, 'student'):
            student = user.student
            structure = getattr(student, 'structure', None)

            data['userType'] = 'Student'
            data['fullName'] = student.name
            data['nationalId'] = student.national_id
            data['academicYear'] = structure.get_year_display() if structure else None
            data['department'] = structure.get_department_display() if structure else None

        elif hasattr(user, 'doctor'):
            doctor = user.doctor
            data['userType'] = 'Staff'
            data['fullName'] = doctor.name
            data['nationalId'] = doctor.national_id

            # نرجع كل الأقسام والسنين اللي الدكتور بيدرس فيها
            structures = doctor.structures.all()
            data['academicYear'] = [s.get_year_display() for s in structures]
            data['department'] = [s.get_department_display() for s in structures]

        else:
            data['userType'] = 'Other'

        return data