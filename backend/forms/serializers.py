from rest_framework import serializers
from .models import Form, Question, Option, Submission, Answer

class OptionSerializer(serializers.ModelSerializer):
    # Accept integer for triggers_question, do not validate existence here
    triggers_question = serializers.SerializerMethodField()

    def get_triggers_question(self, obj):
        return obj.triggers_question.id if obj.triggers_question else None
    class Meta:
        model = Option
        fields = ['id', 'text', 'triggers_question']


# --- Section Support ---
class SectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)
    section_id = serializers.IntegerField(required=False, allow_null=True)
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'question_type', 'order', 'output_template', 'hidden',
            'any_option_triggers_question', 'options', 'section_id'
        ]

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

    def create(self, validated_data):
        import sys
        print("[FormSerializer.create] validated_data IN:", validated_data, file=sys.stderr)
        questions_data = validated_data.pop('questions', [])
        sections_data = validated_data.pop('sections', [])
        print(f"[FormSerializer.create] RAW questions_data: {questions_data}", file=sys.stderr)
        print(f"[FormSerializer.create] RAW sections_data: {sections_data}", file=sys.stderr)
        print(f"[FormSerializer.create] validated_data after pop: {validated_data}", file=sys.stderr)
        # Defensive: ensure section_id is int or None
        for q in questions_data:
            print(f"[FormSerializer.create] Pre section_id: {q.get('section_id')}", file=sys.stderr)
            if 'section_id' in q and q['section_id'] is not None:
                try:
                    q['section_id'] = int(q['section_id'])
                except Exception as exc:
                    print(f"[FormSerializer.create] Failed to cast section_id: {exc}", file=sys.stderr)
                    q['section_id'] = None
            print(f"[FormSerializer.create] Post section_id: {q.get('section_id')}", file=sys.stderr)
        # Store sections as JSON in form.description for round-trip (optional, not for querying)
        try:
            form = Form.objects.create(**validated_data)
            print(f"[FormSerializer.create] Created form: {form}", file=sys.stderr)
            # Save sections to the model's sections field
            form.sections = sections_data if sections_data else []
            form.save()
        except Exception as e:
            print(f"[FormSerializer.create] ERROR creating form: {e}", file=sys.stderr)
            raise
        if sections_data:
            import json as _json
            form.description = (form.description or '') + f"\n__SECTIONS__:{_json.dumps(sections_data)}"
            form.save()
            print(f"[FormSerializer.create] Saved sections to description", file=sys.stderr)
        # Create questions
        question_map = {}
        for q_data in questions_data:
            options_data = q_data.pop('options', [])
            q_id = q_data.get('id', None)
            print(f"[FormSerializer.create] Creating question with data: {q_data}", file=sys.stderr)
            try:
                question = Question.objects.create(form=form, **q_data)
            except Exception as qe:
                print(f"[FormSerializer.create] ERROR creating question: {qe} | data: {q_data}", file=sys.stderr)
                raise
            if q_id is not None:
                question_map[q_id] = question
            else:
                question_map[question.pk] = question
            question._options_data = options_data
        for question in question_map.values():
            for o_data in getattr(question, '_options_data', []):
                triggers_q = o_data.pop('triggers_question', None)
                try:
                    option = Option.objects.create(question=question, text=o_data.get('text', ''), **{k: v for k, v in o_data.items() if k not in ('id', 'text')})
                except Exception as oe:
                    print(f"[FormSerializer.create] ERROR creating option: {oe} | data: {o_data}", file=sys.stderr)
                    raise
                if triggers_q is not None:
                    triggers_instance = question_map.get(triggers_q) or Question.objects.filter(pk=triggers_q, form=form).first()
                    option.triggers_question = triggers_instance if triggers_instance else None
                else:
                    option.triggers_question = None
                option.save()
        print(f"[FormSerializer.create] Form creation complete", file=sys.stderr)
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
        all_options = []
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
                all_options.append((option, triggers_q))
                option.save()
                keep_options.append(option.pk)
            Option.objects.filter(question=question).exclude(id__in=keep_options).delete()
        print(f"[FormSerializer.update] all_options triggers_q: {[tq for _, tq in all_options]}", file=sys.stderr)
        for option, triggers_q in all_options:
            if triggers_q is not None:
                mapped_id = old_to_new_id.get(triggers_q, triggers_q)
                triggers_instance = question_map.get(mapped_id) or Question.objects.filter(pk=mapped_id, form=instance).first()
                option.triggers_question = triggers_instance if triggers_instance else None
                print(f"[FormSerializer.update] Setting triggers_question for option {option.id}: triggers_q={triggers_q}, mapped_id={mapped_id}, triggers_instance_id={getattr(triggers_instance, 'id', None)}", file=sys.stderr)
            else:
                option.triggers_question = None
            option.save()
        Question.objects.filter(form=instance).exclude(id__in=keep_questions).delete()
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
