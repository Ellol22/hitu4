from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from structure.models import StudentStructure, DepartmentChoices, AcademicYearChoices, SemesterChoices
from schedule.models import Schedule
from courses.models import Course
from accounts.models import Doctor  # استورد موديل الدكتور والمعيد
from datetime import datetime
import json
import os
import difflib
import re

class Command(BaseCommand):
    help = 'Load AI schedule data from JSON file with smart course and instructor name matching'

    def clean_instructor_name(self, name):
        """
        تنظيف اسم المعيد/الدكتور من بادئات مثل dr.، eng.، د.، م.، وغيرها.
        ويحول الاسم إلى صيغة موحدة (مثلاً بدون مسافات زائدة)
        """
        if not name:
            return ''

        # تحويل الحروف لصيغة صغيرة للتوحيد
        name = name.lower().strip()

        # إزالة بادئات شائعة (يمكن تعديل القائمة حسب الحاجة)
        prefixes = ['dr.', 'dr', 'eng.', 'eng', 'م.', 'د.', 'دكتور', 'مهندس', 'د']

        for prefix in prefixes:
            # نزيل البادئة لو كانت في بداية الاسم
            if name.startswith(prefix):
                name = name[len(prefix):].strip()

        # تحويل الحروف الأولى لكل كلمة إلى كبيرة (للتوحيد)
        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def get_instructor_instance(self, raw_name):
        """
        نستخدم هذا الدالة لإيجاد المعيد أو الدكتور حسب الاسم بعد التنظيف
        تستخدم البحث بالاسم و لو لم تجد تطابق مباشر، تحاول تطابق قريب
        """
        name = self.clean_instructor_name(raw_name)

        # نجرب نجيب الدكتور مباشرة بالاسم بعد التنظيف
        try:
            return Doctor.objects.get(name=name)
        except Doctor.DoesNotExist:
            # لو لم يجد، نبحث عن أسماء قريبة بالاسم في قاعدة البيانات
            all_names = Doctor.objects.values_list('name', flat=True)
            close_matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.6)
            if close_matches:
                matched_name = close_matches[0]
                self.stdout.write(self.style.WARNING(
                    f"⚠️ Using closest match for instructor '{raw_name}': '{matched_name}'"
                ))
                return Doctor.objects.get(name=matched_name)

        self.stdout.write(self.style.ERROR(
            f"❌ Instructor '{raw_name}' not found in Doctors table."
        ))
        return None

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, '..', '..', 'json', 'ai_schedule.json')

        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        year_map = {
            'year_1': AcademicYearChoices.FIRST,
            'year_2': AcademicYearChoices.SECOND,
            'year_3': AcademicYearChoices.THIRD,
            'year_4': AcademicYearChoices.FOURTH,
        }

        semester_map = {
            'term_1': SemesterChoices.FIRST,
            'term_2': SemesterChoices.SECOND,
        }

        department_map = {
            'ai_department': DepartmentChoices.AI,
            'data_department': DepartmentChoices.DATA,
            'cyber_department': DepartmentChoices.CYBER,
            'autotronics_department': DepartmentChoices.AUTOTRONICS,
            'mechatronics_department': DepartmentChoices.MECHATRONICS,
            'garment_manufacturing_department': DepartmentChoices.GARMENT_MANUFACTURING,
            'control_systems_department': DepartmentChoices.CONTROL_SYSTEMS,
        }

        for department_key, years_dict in json_data.items():
            department_val = department_map.get(department_key)
            if not department_val:
                self.stdout.write(self.style.WARNING(f"Unknown department key in JSON: {department_key}"))
                continue

            for year_key, terms_dict in years_dict.items():
                year_val = year_map.get(year_key)
                if not year_val:
                    self.stdout.write(self.style.WARNING(f"Unknown year key in JSON: {year_key}"))
                    continue

                for term_key, schedules_list in terms_dict.items():
                    semester_val = semester_map.get(term_key)
                    if not semester_val:
                        self.stdout.write(self.style.WARNING(f"Unknown semester key in JSON: {term_key}"))
                        continue

                    try:
                        student_structure = StudentStructure.objects.get(
                            department=department_val,
                            year=year_val,
                            semester=semester_val
                        )
                    except ObjectDoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"StudentStructure not found for department {department_val}, year {year_val}, semester {semester_val}"
                        ))
                        continue

                    # حذف الجدول القديم
                    Schedule.objects.filter(student_structure=student_structure).delete()

                    # احضر أسماء الكورسات المتاحة للبحث الذكي
                    all_courses = Course.objects.filter(
                        department=department_val,
                        academic_year=year_val,
                        semester=semester_val
                    )
                    course_names = [course.name for course in all_courses]

                    for sched in schedules_list:
                        section = sched.get('section', '').strip()
                        start_time = datetime.strptime(sched['start_time'], '%H:%M').time()
                        end_time = datetime.strptime(sched['end_time'], '%H:%M').time()
                        original_name = sched.get('course')

                        try:
                            course = Course.objects.get(
                                name=original_name,
                                department=department_val,
                                academic_year=year_val,
                                semester=semester_val
                            )
                        except Course.DoesNotExist:
                            # لو مش لاقي الاسم، نحاول نلاقي أقرب اسم مشابه
                            close_match = difflib.get_close_matches(original_name, course_names, n=1, cutoff=0.6)
                            if close_match:
                                matched_name = close_match[0]
                                course = Course.objects.get(
                                    name=matched_name,
                                    department=department_val,
                                    academic_year=year_val,
                                    semester=semester_val
                                )
                                self.stdout.write(self.style.WARNING(
                                    f"⚠️ Using closest match for '{original_name}': '{matched_name}'"
                                ))
                            else:
                                self.stdout.write(self.style.ERROR(
                                    f"❌ Course '{original_name}' not found for dept={department_val}, year={year_val}, term={semester_val}"
                                ))
                                continue

                        # استدعاء الدالة الذكية لإيجاد المعيد/الدكتور
                        instructor_instance = self.get_instructor_instance(sched.get('instructor'))

                        schedule_obj = Schedule(
                            student_structure=student_structure,
                            day=sched['day'],
                            slot_number=sched['slot_number'],
                            start_time=start_time,
                            end_time=end_time,
                            section=section,
                            course=course,
                            instructor=instructor_instance,
                            room=sched['room'],
                        )
                        schedule_obj.save()

                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Schedule loaded for {student_structure}"
                    ))

        self.stdout.write(self.style.SUCCESS("🎉 All schedules loaded successfully."))
