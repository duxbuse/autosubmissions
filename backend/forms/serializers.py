from rest_framework import serializers
from .models import Form, Question, Option, Submission, Answer


class FlexiblePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        # We override the validation to allow for temporary IDs
        # that will be resolved in the serializer's update/create method.
        return data


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
    triggers_question = FlexiblePrimaryKeyRelatedField(
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




    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Ensure description is just the plain description, not JSON or with sections
        rep['description'] = instance.description if hasattr(instance, 'description') else rep.get('description', '')
        return rep

    def create(self, validated_data):
        questions_data = self.initial_data.get('questions', [])
        sections_data = validated_data.pop('sections', [])
        
        form_data = {k:v for k,v in validated_data.items() if k not in ['sections', 'questions']}
        form_data['sections'] = sections_data if sections_data else []
        
        form = Form.objects.create(**form_data)

        question_instance_map = {}

        for q_data in questions_data:
            temp_id = q_data.get('id')
            creation_data = {k: v for k, v in q_data.items() if k not in ['id', 'options', 'triggers_question']}
            new_question = Question.objects.create(form=form, **creation_data)
            if temp_id is not None:
                question_instance_map[temp_id] = new_question

        for q_data in questions_data:
            temp_id = q_data.get('id')
            if temp_id not in question_instance_map:
                continue
            q_instance = question_instance_map[temp_id]

            triggers_data = q_data.get('triggers_question', [])
            trigger_ids = [int(t) for t in triggers_data]
            trigger_instances = [question_instance_map[t_id] for t_id in trigger_ids if t_id in question_instance_map]
            q_instance.triggers_question.set(trigger_instances)

            options_data = q_data.get('options', [])
            for o_data in options_data:
                opt_triggers_data = o_data.get('triggers_question', [])
                opt_creation_data = {k: v for k, v in o_data.items() if k not in ['id', 'triggers_question']}
                new_option = Option.objects.create(question=q_instance, **opt_creation_data)

                opt_trigger_ids = [int(t) for t in opt_triggers_data]
                opt_trigger_instances = [question_instance_map[t_id] for t_id in opt_trigger_ids if t_id in question_instance_map]
                new_option.triggers_question.set(opt_trigger_instances)

        return form

    def update(self, instance, validated_data):
        questions_data = self.initial_data.get('questions', [])
        sections_data = validated_data.pop('sections', [])

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.sections = sections_data
        instance.save()

        existing_question_instances = {q.id: q for q in instance.questions.all()}
        incoming_questions_map = {q_data['id']: q_data for q_data in questions_data if 'id' in q_data}
        
        question_instance_map = {}

        for q_id, q_instance in existing_question_instances.items():
            if q_id not in incoming_questions_map:
                q_instance.delete()

        for q_id, q_data in incoming_questions_map.items():
            creation_data = {k: v for k, v in q_data.items() if k not in ['id', 'options', 'triggers_question']}
            
            if q_id in existing_question_instances:
                q_instance = existing_question_instances[q_id]
                for attr, value in creation_data.items():
                    setattr(q_instance, attr, value)
                q_instance.save()
                question_instance_map[q_id] = q_instance
            else:
                q_instance = Question.objects.create(form=instance, **creation_data)
                question_instance_map[q_id] = q_instance

        for q_id, q_data in incoming_questions_map.items():
            q_instance = question_instance_map[q_id]

            triggers_data = q_data.get('triggers_question', [])
            trigger_ids = [int(t) for t in triggers_data]
            trigger_instances = [question_instance_map[t_id] for t_id in trigger_ids if t_id in question_instance_map]
            q_instance.triggers_question.set(trigger_instances)

            options_data = q_data.get('options', [])
            existing_options = {opt.id: opt for opt in q_instance.options.all()}
            incoming_option_ids = {o_data['id'] for o_data in options_data if 'id' in o_data}

            for o_id, o_instance in existing_options.items():
                if o_id not in incoming_option_ids:
                    o_instance.delete()

            for o_data in options_data:
                o_id = o_data.get('id')
                triggers_data_opt = o_data.get('triggers_question', [])
                
                opt_creation_data = {k: v for k, v in o_data.items() if k not in ['id', 'triggers_question']}

                if o_id and o_id in existing_options:
                    opt_instance = existing_options[o_id]
                    opt_instance.text = opt_creation_data.get('text', opt_instance.text)
                    opt_instance.save()
                else:
                    opt_instance = Option.objects.create(question=q_instance, **opt_creation_data)

                trigger_ids_opt = [int(t) for t in triggers_data_opt]
                trigger_instances_opt = [question_instance_map[t_id] for t_id in trigger_ids_opt if t_id in question_instance_map]
                opt_instance.triggers_question.set(trigger_instances_opt)

        return instance

class AnswerSerializer(serializers.ModelSerializer):
    value = serializers.CharField(allow_blank=True)
    class Meta:
        model = Answer
        fields = ['id', 'question', 'value']

class SubmissionSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField(read_only=True)
    answers = AnswerSerializer(many=True)
    submission_date = serializers.DateField()

    class Meta:
        model = Submission
        fields = ['id', 'form', 'client_honorific', 'client_first_name', 'client_surname', 'client_name', 'submission_date', 'submitted_at', 'answers']

    def get_client_name(self, obj):
        return obj.client_name

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])
        # Update main fields
        instance.client_honorific = validated_data.get('client_honorific', instance.client_honorific)
        instance.client_first_name = validated_data.get('client_first_name', instance.client_first_name)
        instance.client_surname = validated_data.get('client_surname', instance.client_surname)
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
