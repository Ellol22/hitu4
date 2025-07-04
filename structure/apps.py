# structure/apps.py

from django.apps import AppConfig


class StructureConfig(AppConfig):
    name = 'structure'

    def ready(self):
        from accounts.models import Student
        from structure.views import update_student_structure, finalize_after_summer
        from structure.models import StudentStructure
        from django.utils import timezone
        import datetime

        today = timezone.now().date()

        # مواعيد التنفيذ اللي اتفقنا عليها:
        run_dates = [
            datetime.date(today.year, 2, 1),
            datetime.date(today.year, 7, 1),
            datetime.date(today.year, 9, 1),
        ]

        if today in run_dates:
            print(f"[CRON READY] Running scheduled student structure update for date: {today}")

            students = Student.objects.all()

            for student in students:
                try:
                    structure = student.structure
                except StudentStructure.DoesNotExist:
                    print(f"[CRON READY] StudentStructure not found for student {student.user.username}, skipping.")
                    continue

                # Logic حسب التاريخ:
                if today == datetime.date(today.year, 2, 1):
                    # بعد ترم أول → تحديث حالة الطالب
                    result = update_student_structure(student)
                    print(f"[1/2] Updated {student.user.username}: {result}")

                elif today == datetime.date(today.year, 7, 1):
                    # بعد ترم ثاني → تحديث حالة الطالب
                    result = update_student_structure(student)
                    print(f"[1/7] Updated {student.user.username}: {result}")

                elif today == datetime.date(today.year, 9, 1):
                    # بعد السمر → finalize
                    result = finalize_after_summer(student)
                    print(f"[1/9] Finalized {student.user.username}: {result}")

        else:
            print(f"[CRON READY] Today {today} is not a scheduled run date.")
