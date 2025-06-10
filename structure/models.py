from django.db import models

# الأقسام
class DepartmentChoices(models.TextChoices):
    AI = 'AI', 'Artificial Intelligence'
    DATA = 'DATA', 'Data Sceince'
    CYBER = 'CYBER', 'Cyber Security'
    AUTOTRONICS = 'AUTOTRONICS', 'Autotronics'
    MECHATRONICS = 'MECHATRONICS', 'Mechatronics'
    GARMENT_MANUFACTURING = 'GARMENT_MANUFACTURING', 'Garment Manufacturing'
    CONTROL_SYSTEMS = 'CONTROL_SYSTEMS', 'Control Systems'

# الفرق الدراسية
class AcademicYearChoices(models.TextChoices):
    FIRST = 'First', 'First Year'
    SECOND = 'Second', 'Second Year'
    THIRD = 'Third', 'Third Year'
    FOURTH = 'Fourth', 'Fourth Year'

# الترم
class SemesterChoices(models.TextChoices):
    FIRST = 'First', 'First Semester'
    SECOND = 'Second', 'Second Semester'
    
class StudentStatusChoices(models.TextChoices):
    PASSED = 'passed', 'Passed'
    SUMMER = 'summer', 'Summer Course'
    RETAKE_YEAR = 'retake_year', 'Retake Year'

class StudentStructure(models.Model):
    department = models.CharField(max_length=25, choices=DepartmentChoices.choices)
    year = models.CharField(max_length=6, choices=AcademicYearChoices.choices)
    semester = models.CharField(max_length=6, choices=SemesterChoices.choices)
    status = models.CharField(max_length=20, choices=StudentStatusChoices.choices, default=StudentStatusChoices.PASSED)

    def __str__(self):
        return f"{self.get_department_display()} - {self.get_year_display()} - {self.get_semester_display()} - {self.get_status_display()}"
