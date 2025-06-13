from django.db import models
from accounts.models import Doctor, Student
from structure.models import DepartmentChoices, AcademicYearChoices, SemesterChoices, StudentStructure

class Course(models.Model):
    name = models.CharField(max_length=255)  # اسم المادة
    structure = models.ForeignKey(StudentStructure, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, blank=True, null=True, limit_choices_to={'role': 'subject_doctor'}, related_name='courses')

    def __str__(self):
        return f"{self.name} - {self.structure.department} - {self.structure.year} - {self.structure.semester}"


# جدول يربط الطالب بالمواد بناءً على هيكل الطالب
class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)  # الطالب
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # المادة

    def __str__(self):
        return f"{self.student.name} - {self.course.name}"
    


class CourseSectionAssistant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='section_assistants')
    section = models.CharField(max_length=10)  # مثلاً: "Sec 1", "Sec 2", "Sec 3"
    assistant = models.ForeignKey(Doctor, on_delete=models.CASCADE, limit_choices_to={'role': 'teaching_assistant'})

    def __str__(self):
        return f"{self.course.name} - {self.section} - {self.assistant.name}"
