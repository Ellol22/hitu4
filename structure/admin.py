from django.contrib import admin
from .models import StudentStructure

@admin.register(StudentStructure)
class StudentStructureAdmin(admin.ModelAdmin):
    search_fields = ['department', 'year', 'semester']
