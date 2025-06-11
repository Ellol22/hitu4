# serializers.py
from rest_framework import serializers
from .models import Task, Submission

class SubmissionSerializer(serializers.ModelSerializer):
    submittedFile = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ['submittedFile', 'completed']

    def get_submittedFile(self, obj):
        return obj.submitted_file.url if obj.submitted_file else None


class TaskSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()
    submittedFile = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['title', 'due_date', 'completed', 'files', 'description', 'submittedFile']

    def get_files(self, obj):
        return [obj.files.url] if obj.files else []

    def get_submittedFile(self, obj):
        student = self.context.get('student')
        if not student:
            return None
        submission = Submission.objects.filter(task=obj, student=student).first()
        return submission.submitted_file.url if submission and submission.submitted_file else None

    def get_completed(self, obj):
        student = self.context.get('student')
        if not student:
            return False
        submission = Submission.objects.filter(task=obj, student=student).first()
        return submission.completed if submission else False