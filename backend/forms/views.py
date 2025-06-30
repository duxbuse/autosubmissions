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
        # Save form and questions/options
        try:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Serializer error in FormViewSet.update: {e}\nData: {data}\nErrors: {getattr(e, 'detail', str(e))}")
            return Response({'detail': 'Invalid data', 'errors': getattr(e, 'detail', str(e))}, status=400)
        self.perform_update(serializer)
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
        # Placeholder for document generation logic
        return Response({'status': 'Document generation not implemented yet.'})
