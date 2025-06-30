from rest_framework import serializers
from .models import Form, Question, Option, Submission, Answer

class OptionSerializer(serializers.ModelSerializer):
    # Accept integer for triggers_question, do not validate existence here
    triggers_question = serializers.IntegerField(allow_null=True, required=False)
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
        # First pass: create all questions, keep mapping of id to question
        question_map = {}
        for q_data in questions_data:
            options_data = q_data.pop('options', [])
            q_id = q_data.get('id', None)
            question = Question.objects.create(form=form, **q_data)
            if q_id is not None:
                question_map[q_id] = question
            else:
                question_map[question.pk] = question
            question._options_data = options_data
        # Second pass: create all options, resolve triggers_question
        for question in question_map.values():
            for o_data in getattr(question, '_options_data', []):
                triggers_q = o_data.pop('triggers_question', None)
                option = Option.objects.create(question=question, text=o_data.get('text', ''), **{k: v for k, v in o_data.items() if k not in ('id', 'text')})
                if triggers_q:
                    # Only assign if the referenced question exists in this form
                    triggers_instance = question_map.get(triggers_q) or Question.objects.filter(pk=triggers_q, form=form).first()
                    if triggers_instance:
                        option.triggers_question = triggers_instance
                        option.save()
        return form

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        # First pass: update or create all questions, keep mapping
        keep_questions = []
        question_map = {}
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
                q_id = question.pk
            keep_questions.append(question.pk)
            question_map[q_id] = question
            question._options_data = options_data

        # Second pass: update/create all options, resolve triggers_question
        for question in question_map.values():
            keep_options = []
            for o_data in getattr(question, '_options_data', []):
                o_id = o_data.get('id', None)
                triggers_q = o_data.pop('triggers_question', None)
                if o_id:
                    option = Option.objects.get(id=o_id, question=question)
                    for attr, value in o_data.items():
                        setattr(option, attr, value)
                else:
                    option = Option.objects.create(question=question, text=o_data.get('text', ''), **{k: v for k, v in o_data.items() if k not in ('id', 'text')})
                if triggers_q:
                    triggers_instance = question_map.get(triggers_q) or Question.objects.filter(pk=triggers_q, form=instance).first()
                    if triggers_instance:
                        option.triggers_question = triggers_instance
                option.save()
                keep_options.append(option.pk)
            Option.objects.filter(question=question).exclude(id__in=keep_options).delete()

        # Delete removed questions
        Question.objects.filter(form=instance).exclude(id__in=keep_questions).delete()

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
