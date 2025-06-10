from django.core.management.base import BaseCommand
from accounts.models import Student
from courses.models import Course, StudentCourse

class Command(BaseCommand):
    help = 'Assign students to courses based on their structure'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        courses = Course.objects.all()
        count = 0

        for student in students:
            for course in courses:
                if (student.structure and
                    student.structure.department == course.department and
                    student.structure.year == course.academic_year and
                    student.structure.semester == course.semester):

                    _, created = StudentCourse.objects.get_or_create(
                        student=student,
                        course=course
                    )
                    if created:
                        count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Assigned {count} student-course relations.'))

# python manage.py assign_students_to_courses