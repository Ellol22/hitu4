from django.db import models
from django.contrib.auth.models import User
from structure.models import StudentStructure


class Student(models.Model):
    user =models.OneToOneField(User , on_delete=models.CASCADE , blank=True , null=True)
    name =models.CharField(max_length=25)
    mobile =models.CharField(max_length=11 , blank=True , null=True)
    national_id =models.CharField(max_length=14)
    sec_num = models.IntegerField(null=True, blank=True)
    structure = models.ForeignKey(StudentStructure, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__ (self):
        return (self.name)
    
    def get_my_courses(self):
        from courses.models import Course
        if self.structure:
            return Course.objects.filter(
                department=self.structure.department,
                academic_year=self.structure.year,
                semester=self.structure.semester
            )
        return Course.objects.none()

class DoctorRole(models.TextChoices):
    SUBJECT_DOCTOR = 'subject_doctor', 'دكتور مادة'
    ADMIN_DOCTOR = 'admin_doctor', 'دكتور إداري'
    TEACHING_ASSISTANT = 'teaching_assistant', 'معيد'



class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=25)
    mobile = models.CharField(max_length=11, blank=True, null=True)
    national_id = models.CharField(max_length=14, unique=True)  # مهم لربطه بالحساب لاحقًا
    role = models.CharField(
        max_length=20,
        choices=DoctorRole.choices,
        default=DoctorRole.SUBJECT_DOCTOR
    )

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    def get_my_courses(self):
        from courses.models import Course
        return Course.objects.filter(
            id__in=self.course_assignments.values_list('course_id', flat=True)
        )
