from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Form, Question, Option, Submission, Answer
from .serializers import FormSerializer, SubmissionSerializer
import json
from django.conf import settings
from pathlib import Path
import logging
from django.http import HttpResponse
from docx import Document
import re

class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        logger = logging.getLogger(__name__)
        logger.info(f"[FormViewSet.update] Incoming payload: {json.dumps(data, indent=2)}")
        # Save form and questions/options
        try:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(f"Serializer error in FormViewSet.update: {e}\nData: {data}\nErrors: {getattr(e, 'detail', str(e))}")
            return Response({'detail': 'Invalid data', 'errors': getattr(e, 'detail', str(e))}, status=400)
        self.perform_update(serializer)
        # Log serialized data after update
        logger.info(f"[FormViewSet.update] Serialized response: {json.dumps(serializer.data, indent=2)}")
        # Compare payload and serialized data for divergence
        if json.dumps(data, sort_keys=True) != json.dumps(serializer.data, sort_keys=True):
            logger.warning(f"[FormViewSet.update] Payload and serialized data diverge!\nPayload: {json.dumps(data, indent=2)}\nSerialized: {json.dumps(serializer.data, indent=2)}")
        # Write to JSON file
        forms_dir = Path(settings.BASE_DIR) / 'form_json'
        forms_dir.mkdir(exist_ok=True)
        file_path = forms_dir / f'form_{instance.id}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializer.data, f, ensure_ascii=False, indent=2)
        return Response(serializer.data)

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    @action(detail=True, methods=['get'])
    def generate_doc(self, request, pk=None):
        submission = get_object_or_404(Submission, pk=pk)
        answers = {a.question.pk: a.value for a in submission.answers.all()}
        questions = Question.objects.filter(form=submission.form).order_by('order')
        doc = Document()
        for q in questions:
            template = q.output_template or ''
            answer = answers.get(q.pk, '')
            # Only add template if answer is not blank/null
            if answer is not None and str(answer).strip() != '':
                text = template.replace('{{answer}}', str(answer))
                if text.strip():
                    doc.add_paragraph(text)
        from io import BytesIO
        f = BytesIO()
        doc.save(f)
        f.seek(0)
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="submission_{submission.pk}.docx"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"[SubmissionViewSet.create] Incoming data: {json.dumps(request.data, indent=2)}")
        # Write the incoming submission data to a local JSON file for debugging
        try:
            from django.conf import settings
            from pathlib import Path
            submissions_dir = Path(settings.BASE_DIR) / 'submission_json'
            submissions_dir.mkdir(exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = submissions_dir / f'submission_{timestamp}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(request.data, f, ensure_ascii=False, indent=2)
            logger.info(f"[SubmissionViewSet.create] Wrote submission to {file_path}")
        except Exception as file_exc:
            logger.error(f"[SubmissionViewSet.create] Failed to write submission JSON: {file_exc}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"[SubmissionViewSet.create] Response: {response.status_code} {getattr(response, 'data', None)}")
            return response
        except Exception as e:
            logger.error(f"[SubmissionViewSet.create] Exception: {str(e)}", exc_info=True)
            from rest_framework.views import exception_handler
            resp = exception_handler(e, context={'view': self, 'request': request})
            logger.error(f"[SubmissionViewSet.create] DRF exception handler response: {getattr(resp, 'data', None)}")
            return resp or Response({'detail': str(e)}, status=400)
