from django.contrib import admin
from .models import (
    Quiz, QuizQuestion, QuizSubmission, QuizAnswer,
    Assignment, AssignmentFile, Submission
)


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_time', 'end_time', 'created_by', 'created_at')
    list_filter = ('course', 'created_by', 'start_time')
    search_fields = ('title', 'course__name')
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'correct_option')
    search_fields = ('text', 'quiz__title')
    list_filter = ('quiz',)


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'status', 'submitted_at')
    list_filter = ('quiz', 'status')
    search_fields = ('student__user__username', 'quiz__title')
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('submission', 'question', 'selected_option')
    list_filter = ('question__quiz',)
    search_fields = ('question__text',)


class AssignmentFileInline(admin.TabularInline):
    model = AssignmentFile
    extra = 1


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'created_by', 'created_at')
    list_filter = ('course', 'created_by')
    search_fields = ('title', 'course__name')
    inlines = [AssignmentFileInline]


@admin.register(AssignmentFile)
class AssignmentFileAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'file', 'uploaded_at')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at')
    list_filter = ('assignment',)
    search_fields = ('assignment__title', 'student__user__username')
