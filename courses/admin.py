# admin.py
from django.contrib import admin
from .models import Course, StudentCourse, CourseSectionAssistant
from structure.models import StudentStructure

class CourseSectionAssistantInline(admin.TabularInline):
    model = CourseSectionAssistant
    extra = 1  # عدد السطور الفاضية الجاهزة للإضافة
    verbose_name = "معيد للقسم"
    verbose_name_plural = "المعيدين المرتبطين بالأقسام"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'structure', 'doctor')
    list_filter = ('structure__department', 'structure__year', 'structure__semester')
    search_fields = ('name',)
    ordering = ('structure__department', 'structure__year', 'structure__semester')
    inlines = [CourseSectionAssistantInline]
    
    fieldsets = (
        ('معلومات المادة', {
            'fields': ('name', 'structure', 'doctor')
        }),
    )

    # # لإظهار القيم القديمة في list_display
    # def get_department(self, obj):
    #     return obj.structure.get_department_display() if obj.structure else '-'
    # get_department.short_description = 'Department'

    # def get_academic_year(self, obj):
    #     return obj.structure.get_year_display() if obj.structure else '-'
    # get_academic_year.short_description = 'Academic Year'

    # def get_semester(self, obj):
    #     return obj.structure.get_semester_display() if obj.structure else '-'
    # get_semester.short_description = 'Semester'

@admin.register(StudentCourse)
class StudentCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course')
    search_fields = ('student__name', 'course__name')
    list_filter = ('course__structure__department', 'course__structure__year', 'course__structure__semester')
