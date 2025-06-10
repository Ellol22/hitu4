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
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # تحديد نوع اليوزر
        if hasattr(user, 'student'):
            data['userType'] = 'Student'

            # لو طالب هضيف البيانات المطلوبة
            student = user.student
            structure = student.structure

            data.update({
                'fullName': student.name,
                'nationalId': student.national_id,
                'academicYear': structure.get_year_display() if structure else None,
                'department': structure.get_department_display() if structure else None,
            })

        elif hasattr(user, 'doctor'):
            data['userType'] = 'Staff'  # أو 'Doctor' حسب ما تفضل

            # لو حابب نضيف بيانات الدكتور كمان ممكن نزود هنا

        else:
            data['userType'] = 'Unknown'

        return data

