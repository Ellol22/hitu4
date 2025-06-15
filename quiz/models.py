from django.db import models
from accounts.models import Doctor, Student
from structure.models import StudentStructure
from courses.models import Course  # Import Course if not already imported

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    duration = models.PositiveIntegerField(default=30)  # Duration in minutes
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.name}"

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.PositiveSmallIntegerField(choices=[(i, f"Option {i+1}") for i in range(4)])

    def __str__(self):
        return f"Question: {self.text} (Quiz: {self.quiz.title})"

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.name}"

class AssignmentFile(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='assignments/files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File: {self.file.name} (Assignment: {self.assignment.title})"