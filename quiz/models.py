from django.db import models
from accounts.models import Doctor, Student
from structure.models import StudentStructure
from courses.models import Course  # Import Course if not already imported

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
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

class QuizSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=[('not_started', 'Not Started'), ('ended', 'Ended')], default='not_started')

    class Meta:
        unique_together = ('student', 'quiz')

    def calculate_score(self):
        correct_answers = 0
        total_questions = self.answers.count()
        for answer in self.answers.all():
            if answer.selected_option == answer.question.correct_option:
                correct_answers += 1
        self.score = (correct_answers / total_questions) * 100 if total_questions else 0
        self.save()

class QuizAnswer(models.Model):
    submission = models.ForeignKey(QuizSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('submission', 'question')  # ✅ عشان ميتسجلش إجابة لنفس السؤال مرتين

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='assignments/submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']  # ✅ علشان الأحدث يظهر أولًا (لو حبيتِ في الواجهة)