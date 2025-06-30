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

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        form = Form.objects.create(**validated_data)
        for q_data in questions_data:
            options_data = q_data.pop('options', [])
            question = Question.objects.create(form=form, **q_data)
            for o_data in options_data:
                Option.objects.create(question=question, **o_data)
        return form

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        # Update questions
        keep_questions = []
        for q_data in questions_data:
            options_data = q_data.pop('options', [])
            q_id = q_data.get('id', None)
            if q_id:
                question = Question.objects.get(id=q_id, form=instance)
                for attr, value in q_data.items():
                    setattr(question, attr, value)
                question.save()
            else:
                question = Question.objects.create(form=instance, **q_data)
            keep_questions.append(question.id)

            # Update options
            keep_options = []
            for o_data in options_data:
                o_id = o_data.get('id', None)
                if o_id:
                    option = Option.objects.get(id=o_id, question=question)
                    for attr, value in o_data.items():
                        setattr(option, attr, value)
                    option.save()
                else:
                    option = Option.objects.create(question=question, **o_data)
                keep_options.append(option.id)
            # Delete removed options
            question.options.exclude(id__in=keep_options).delete()

        # Delete removed questions
        instance.questions.exclude(id__in=keep_questions).delete()

        return instance

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'value']

class SubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    class Meta:
        model = Submission
        fields = ['id', 'form', 'submitted_at', 'answers']
