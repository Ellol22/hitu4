from django.contrib import admin
from .models import StudentStructure

@admin.register(StudentStructure)
class StudentStructureAdmin(admin.ModelAdmin):
    list_display = ['get_student_username', 'department', 'year', 'semester', 'status', 'failed_courses_display']
    search_fields = ['department', 'year', 'semester', 'status']
    list_filter = ['department', 'year', 'semester', 'status']
    readonly_fields = ['failed_courses_display']

    def get_student_username(self, obj):
        try:
            return obj.student.user.username
        except:
            return "-"
    get_student_username.short_description = 'Student Username'

    def failed_courses_display(self, obj):
        return ", ".join(obj.failed_courses_names or [])
    failed_courses_display.short_description = 'Failed Courses'
