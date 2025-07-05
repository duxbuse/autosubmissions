from rest_framework import serializers
from .models import Form, Question, Option, Submission, Answer


class OptionSerializer(serializers.ModelSerializer):
    # Accept list of question IDs for triggers_question
    triggers_question = serializers.PrimaryKeyRelatedField(
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
            'any_option_triggers_question', 'options', 'section_id', 'triggers_question'
        ]

    def create(self, validated_data):
        triggers = validated_data.pop('triggers_question', [])
        options_data = validated_data.pop('options', []) if 'options' in validated_data else []
        question = Question.objects.create(**validated_data)
        if triggers:
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
        from rest_framework.exceptions import ValidationError
        questions_data = validated_data.pop('questions', [])
        sections_data = validated_data.pop('sections', [])
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        # Save sections to the model's sections field
        instance.sections = sections_data if sections_data else []
        instance.save()
        # --- Debug: Log all current question/option IDs for this form ---
        current_questions = list(Question.objects.filter(form=instance))
        current_question_ids = [q.id for q in current_questions]
        current_option_ids = {q.id: list(Option.objects.filter(question=q).values_list('id', flat=True)) for q in current_questions}
        import sys
        print(f"[FormSerializer.update] Current DB question IDs: {current_question_ids}", file=sys.stderr)
        print(f"[FormSerializer.update] Current DB option IDs: {current_option_ids}", file=sys.stderr)
        payload_question_ids = []
        payload_option_ids = {}
        for q in questions_data:
            qid = q.get('id', None)
            if qid is not None:
                payload_question_ids.append(qid)
            opts = q.get('options', [])
            payload_option_ids[qid] = []
            for o in opts:
                oid = o.get('id', None)
                if oid is not None:
                    payload_option_ids[qid].append(oid)
        print(f"[FormSerializer.update] Payload question IDs: {payload_question_ids}", file=sys.stderr)
        print(f"[FormSerializer.update] Payload option IDs: {payload_option_ids}", file=sys.stderr)
        missing_questions = [qid for qid in payload_question_ids if qid not in current_question_ids]
        missing_options = {}
        for qid, oids in payload_option_ids.items():
            if qid in current_option_ids:
                missing = [oid for oid in oids if oid not in current_option_ids[qid]]
                if missing:
                    missing_options[qid] = missing
            else:
                if oids:
                    missing_options[qid] = oids
        if missing_questions or missing_options:
            print(f"[FormSerializer.update] Refusing update: missing questions: {missing_questions}, missing options: {missing_options}", file=sys.stderr)
            raise ValidationError(f"Update payload contains question/option IDs not present in DB. Missing questions: {missing_questions}, missing options: {missing_options}")
        keep_questions = []
        question_map = {}
        old_to_new_id = {}
        for q_data in questions_data:
            options_data = q_data.pop('options', [])
            q_id = q_data.get('id', None)
            old_id = q_id
            if q_id:
                question = Question.objects.get(id=q_id, form=instance)
                for attr, value in q_data.items():
                    setattr(question, attr, value)
                question.save()
            else:
                question = Question.objects.create(form=instance, **q_data)
                old_id = None
                q_id = question.pk
            keep_questions.append(question.pk)
            question_map[question.pk] = question
            if old_id is not None:
                old_to_new_id[old_id] = question.pk
                question_map[old_id] = question
            question._options_data = options_data
        print(f"[FormSerializer.update] old_to_new_id mapping: {old_to_new_id}", file=sys.stderr)
        print(f"[FormSerializer.update] question_map keys: {list(question_map.keys())}", file=sys.stderr)
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
                # Set ManyToMany triggers_question
                if triggers_q is not None:
                    # triggers_q may be a list or a single value
                    if not isinstance(triggers_q, list):
                        triggers_ids = [triggers_q]
                    else:
                        triggers_ids = triggers_q
                    # Map old IDs to new IDs if needed
                    mapped_ids = [old_to_new_id.get(tid, tid) for tid in triggers_ids if tid is not None]
                    triggers_instances = [question_map.get(mid) or Question.objects.filter(pk=mid, form=instance).first() for mid in mapped_ids]
                    triggers_instances = [ti for ti in triggers_instances if ti]
                    option.triggers_question.set(triggers_instances)
                else:
                    option.triggers_question.clear()
                option.save()
                keep_options.append(option.pk)
            Option.objects.filter(question=question).exclude(id__in=keep_options).delete()
        # Before deleting questions, remove all references to them in triggers_question of all options
        to_delete_questions = Question.objects.filter(form=instance).exclude(id__in=keep_questions)
        to_delete_ids = list(to_delete_questions.values_list('id', flat=True))
        if to_delete_ids:
            # Remove references in Option.triggers_question
            for option in Option.objects.filter(question__form=instance):
                option.triggers_question.remove(*[tid for tid in to_delete_ids if tid in option.triggers_question.values_list('id', flat=True)])
        to_delete_questions.delete()
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
