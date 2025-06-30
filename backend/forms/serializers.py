from rest_framework import serializers
from .models import Form, Question, Option, Submission, Answer

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'triggers_question']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'question_type', 'order', 'output_template', 'hidden',
            'any_option_triggers_question', 'options'
        ]

class FormSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    class Meta:
        model = Form
        fields = ['id', 'name', 'description', 'questions']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'value']

class SubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    class Meta:
        model = Submission
        fields = ['id', 'form', 'submitted_at', 'answers']
