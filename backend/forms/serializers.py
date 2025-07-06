from rest_framework import serializers
from .models import Form, Question, Option, Submission, Answer


class FlexiblePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        try:
            # Try to treat it as a regular PK
            return super().to_internal_value(data)
        except (TypeError, ValueError):
            # If that fails, assume it's a string to be resolved later
            return str(data)


class OptionSerializer(serializers.ModelSerializer):
    triggers_question = FlexiblePrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Option
        fields = ['id', 'text', 'triggers_question']

    def create(self, validated_data):
        triggers = validated_data.pop('triggers_question', [])
        option = Option.objects.create(**validated_data)
        if triggers:
            option.triggers_question.set(triggers)
        return option

    def update(self, instance, validated_data):
        triggers = validated_data.pop('triggers_question', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if triggers is not None:
            instance.triggers_question.set(triggers)
        return instance


# --- Section Support ---
class SectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)
    section_id = serializers.IntegerField(required=False, allow_null=True)
    triggers_question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'question_type', 'order', 'output_template', 'hidden',
            'options', 'section_id', 'triggers_question'
        ]

    def create(self, validated_data):
        triggers = validated_data.pop('triggers_question', [])
        options_data = validated_data.pop('options', []) if 'options' in validated_data else []
        question = Question.objects.create(**validated_data)
        if triggers is not None:
            question.triggers_question.set(triggers)
        # Optionally handle options creation here if needed
        return question

    def update(self, instance, validated_data):
        triggers = validated_data.pop('triggers_question', None)
        options_data = validated_data.pop('options', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if triggers is not None:
            instance.triggers_question.set(triggers)
        return instance

class FormSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, required=False)
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Form
        fields = ['id', 'name', 'description', 'sections', 'questions']


    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'questions' in data:
            ret['questions'] = data['questions']
        if 'sections' in data:
            ret['sections'] = data['sections']
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Ensure description is just the plain description, not JSON or with sections
        rep['description'] = instance.description if hasattr(instance, 'description') else rep.get('description', '')
        return rep

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        sections_data = validated_data.pop('sections', [])
        # Defensive: ensure section_id is int or None
        for q in questions_data:
            if 'section_id' in q and q['section_id'] is not None:
                try:
                    q['section_id'] = int(q['section_id'])
                except Exception:
                    q['section_id'] = None
        # Only store the plain description from validated_data
        form = Form.objects.create(**validated_data)
        # Save sections to the model's sections field (not description)
        form.sections = sections_data if sections_data else []
        form.save()
        # Create questions
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
        for question in question_map.values():
            for o_data in getattr(question, '_options_data', []):
                triggers_q = o_data.pop('triggers_question', None)
                option = Option.objects.create(question=question, text=o_data.get('text', ''), **{k: v for k, v in o_data.items() if k not in ('id', 'text')})
                if triggers_q is not None:
                    triggers_instance = question_map.get(triggers_q) or Question.objects.filter(pk=triggers_q, form=form).first()
                    option.triggers_question = triggers_instance if triggers_instance else None
                else:
                    option.triggers_question = None
                option.save()
        return form

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        sections_data = validated_data.pop('sections', [])

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.sections = sections_data
        instance.save()

        # --- Question & Option Update/Create Logic ---
        existing_questions = {q.id: q for q in instance.questions.all()}
        incoming_question_ids = {q_data['id'] for q_data in questions_data if 'id' in q_data}

        # Delete questions not in the payload
        for q_id, q_instance in existing_questions.items():
            if q_id not in incoming_question_ids:
                q_instance.delete()

        # Create or update questions
        for q_data in questions_data:
            q_id = q_data.get('id')
            if q_id and q_id in existing_questions:
                # Update existing question
                q_instance = existing_questions[q_id]
                q_instance.text = q_data.get('text', q_instance.text)
                q_instance.question_type = q_data.get('question_type', q_instance.question_type)
                q_instance.order = q_data.get('order', q_instance.order)
                q_instance.output_template = q_data.get('output_template', q_instance.output_template)
                q_instance.hidden = q_data.get('hidden', q_instance.hidden)
                q_instance.section_id = q_data.get('section_id', q_instance.section_id)
                q_instance.save()

                # Handle triggers for the question
                triggers_data = q_data.get('triggers_question', [])
                trigger_instances = []
                for trigger in triggers_data:
                    if isinstance(trigger, Question):
                        trigger_instances.append(trigger)
                    elif isinstance(trigger, int):
                        triggered_q = Question.objects.filter(pk=trigger).first()
                        if triggered_q:
                            trigger_instances.append(triggered_q)
                q_instance.triggers_question.set(trigger_instances)
            else:
                # Create new question
                q_data.pop('id', None)
                options_data = q_data.pop('options', [])
                q_instance = Question.objects.create(form=instance, **q_data)

            # Update or create options for the question
            options_data = q_data.get('options', [])
            existing_options = {opt.id: opt for opt in q_instance.options.all()}
            incoming_option_ids = {o_data['id'] for o_data in options_data if 'id' in o_data}

            # Delete options not in the payload
            for o_id, o_instance in existing_options.items():
                if o_id not in incoming_option_ids:
                    o_instance.delete()

            for o_data in options_data:
                o_id = o_data.get('id')
                triggers_data = o_data.pop('triggers_question', [])
                if o_id and o_id in existing_options:
                    # Update existing option
                    opt_instance = existing_options[o_id]
                    opt_instance.text = o_data.get('text', opt_instance.text)
                    opt_instance.save()
                else:
                    # Create new option
                    o_data.pop('id', None)
                    opt_instance = Option.objects.create(question=q_instance, **o_data)

                # Link triggers
                trigger_instances = []
                for trigger in triggers_data:
                    if isinstance(trigger, Question):
                        trigger_instances.append(trigger)
                    elif isinstance(trigger, int):
                        # Find by PK
                        triggered_q = Question.objects.filter(pk=trigger).first()
                        if triggered_q:
                            trigger_instances.append(triggered_q)
                opt_instance.triggers_question.set(trigger_instances)

        return instance

class AnswerSerializer(serializers.ModelSerializer):
    value = serializers.CharField(allow_blank=True)
    class Meta:
        model = Answer
        fields = ['id', 'question', 'value']

class SubmissionSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])
        # Update main fields
        instance.client_name = validated_data.get('client_name', instance.client_name)
        instance.submission_date = validated_data.get('submission_date', instance.submission_date)
        if 'form' in validated_data:
            instance.form_id = int(validated_data['form']) if isinstance(validated_data['form'], str) else validated_data['form']
        instance.save()

        # Remove all old answers and recreate
        instance.answers.all().delete()
        for answer_data in answers_data:
            if 'question' in answer_data and isinstance(answer_data['question'], str):
                answer_data['question'] = int(answer_data['question'])
            Answer.objects.create(submission=instance, **answer_data)
        return instance
    answers = AnswerSerializer(many=True)
    client_name = serializers.CharField()
    submission_date = serializers.DateField()
    class Meta:
        model = Submission
        fields = ['id', 'form', 'client_name', 'submission_date', 'submitted_at', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        # Convert string IDs to integers for 'form' and 'question' fields
        if 'form' in validated_data and isinstance(validated_data['form'], str):
            validated_data['form'] = int(validated_data['form'])
        # Parse date if sent as string
        if 'submission_date' in validated_data and isinstance(validated_data['submission_date'], str):
            from datetime import datetime
            validated_data['submission_date'] = datetime.strptime(validated_data['submission_date'], "%Y-%m-%d").date()
        submission = Submission.objects.create(**validated_data)
        for answer_data in answers_data:
            if 'question' in answer_data and isinstance(answer_data['question'], str):
                answer_data['question'] = int(answer_data['question'])
            Answer.objects.create(submission=submission, **answer_data)
        return submission

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Always include answers in the output, even if not present in the initial payload
        rep['answers'] = AnswerSerializer(instance.answers.all(), many=True).data
        return rep
