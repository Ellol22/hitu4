from rest_framework import serializers
from .models import Quiz, QuizQuestion, Assignment, AssignmentFile
from django.utils import timezone
from courses.models import Course
from datetime import datetime

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'text', 'option1', 'option2', 'option3', 'option4', 'correct_option']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['options'] = [ret.pop('option1'), ret.pop('option2'), ret.pop('option3'), ret.pop('option4')]
        ret['correctOption'] = ret.pop('correct_option')
        return ret

    def to_internal_value(self, data):
        data = data.copy()
        if 'options' in data:
            options = data.pop('options')
            if len(options) != 4:
                raise serializers.ValidationError("Exactly 4 options are required.")
            data['option1'] = options[0]
            data['option2'] = options[1]
            data['option3'] = options[2]
            data['option4'] = options[3]
        if 'correctOption' in data:
            data['correct_option'] = data.pop('correctOption')
        return super().to_internal_value(data)

    def validate_correct_option(self, value):
        if value not in [0, 1, 2, 3]:
            raise serializers.ValidationError("Correct option must be between 0 and 3.")
        return value

class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    startTime = serializers.DateTimeField(source='start_time')
    endTime = serializers.DateTimeField(source='end_time')

    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'questions', 'startTime', 'endTime', 'created_at', 'updated_at']

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError("End time must be after start time.")
            if end_time <= timezone.now():
                raise serializers.ValidationError("End time must be in the future.")
        questions = data.get('questions', [])
        if not questions:
            raise serializers.ValidationError("At least one question is required.")
        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        start_time = ret.get('startTime')
        end_time = ret.get('endTime')
        if start_time and end_time:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = (end - start).total_seconds() / 60  # Duration in minutes
            ret['duration'] = duration
        else:
            ret['duration'] = None
        return ret

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        course = validated_data.pop('course')
        if not hasattr(self.context['request'].user, 'doctor'):
            raise serializers.ValidationError("Only doctors can create quizzes.")
        quiz = Quiz.objects.create(
            course=course,
            created_by=self.context['request'].user.doctor,
            **validated_data
        )
        for question_data in questions_data:
            QuizQuestion.objects.create(quiz=quiz, **question_data)
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        course = validated_data.pop('course', None)
        if course:
            instance.course = course
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            instance.questions.all().delete()
            for question_data in questions_data:
                QuizQuestion.objects.create(quiz=instance, **question_data)
        return instance

class AssignmentFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = AssignmentFile
        fields = ['id', 'file', 'uploaded_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['file_url'] = instance.file.url
        return ret

class AssignmentSerializer(serializers.ModelSerializer):
    files = AssignmentFileSerializer(many=True, read_only=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    uploaded_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = Assignment
        fields = ['id', 'course', 'title', 'deadline', 'files', 'uploaded_files', 'created_at', 'updated_at']

    def validate(self, data):
        deadline = data.get('deadline')
        if deadline and deadline <= timezone.now():
            raise serializers.ValidationError("Deadline must be in the future.")
        return data

    def create(self, validated_data):
        files_data = validated_data.pop('uploaded_files', [])
        course = validated_data.pop('course')
        if not hasattr(self.context['request'].user, 'doctor'):
            raise serializers.ValidationError("Only doctors can create assignments.")
        assignment = Assignment.objects.create(
            course=course,
            created_by=self.context['request'].user.doctor,
            **validated_data
        )
        for file in files_data:
            AssignmentFile.objects.create(assignment=assignment, file=file)
        return assignment

    def update(self, instance, validated_data):
        files_data = validated_data.pop('uploaded_files', None)
        course = validated_data.pop('course', None)
        if course:
            instance.course = course
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if files_data is not None:
            instance.files.all().delete()
            for file in files_data:
                AssignmentFile.objects.create(assignment=instance, file=file)
        return instance