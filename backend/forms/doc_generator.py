from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re
from io import BytesIO
from .models import Submission, Question, Answer

class DocGenerator:
    # Default template configurations for different form types
    DEFAULT_TEMPLATES = {
        'plea_of_guilty': {
            'title': "OUTLINE OF SUBMISSIONS FOR PLEA HEARING",
            'sections': [
                {
                    'name': 'title_page',
                    'type': 'title',
                    'content': {
                        'court': "IN THE MAGISTRATES' COURT",
                        'location': "AT MELBOURNE",
                        'parties': ["VICTORIA POLICE", "and", "{client_name}"]
                    }
                },
                {
                    'name': 'Personal Circumstances',
                    'type': 'section',
                    'use_form_sections': True  # Flag to use sections from the form
                },
            ]
        },
        'bail_application': {
            'title': "BAIL APPLICATION SUBMISSION",
            'sections': [
                {
                    'name': 'title_page',
                    'type': 'title',
                    'content': {
                        'court': "IN THE MAGISTRATES' COURT",
                        'location': "AT MELBOURNE",
                        'parties': ["VICTORIA POLICE", "and", "{client_name}"]
                    }
                },
                {
                    'name': 'Application Details',
                    'type': 'section',
                    'fields': ['Charges', 'Exceptional Circumstances', 'Risk Assessment']
                }
            ]
        }
    }

    def __init__(self, submission: Submission):
        """Initialize with a submission"""
        self.submission = submission
        # Get all answers with their questions
        answers = Answer.objects.select_related('question').filter(submission=submission)
        self.answers_by_question = {a.question.pk: a.value for a in answers}
        questions = Question.objects.filter(form=submission.form).order_by('order')
        self.questions = {q.text.lower(): q for q in questions}
        # Create a map of questions by section ID for efficient lookup
        self.questions_by_section = {}
        for q in questions:
            if q.section_id:
                if q.section_id not in self.questions_by_section:
                    self.questions_by_section[q.section_id] = []
                self.questions_by_section[q.section_id].append(q)
        self.sections = submission.form.sections or []

    def generate(self) -> BytesIO:
        """Generate a document based on the form's template type"""
        template_type = self.submission.form.template_type or 'plea_of_guilty'
        template_config = self.DEFAULT_TEMPLATES.get(template_type, self.DEFAULT_TEMPLATES['plea_of_guilty'])
        
        doc = Document()
        
        # Add header with submission date and client name
        submission_date = self.submission.submission_date.strftime('%B %d, %Y') if self.submission.submission_date else ''
        client_name = self.submission.client_name or 'client'

        # Add header
        header = doc.sections[0].header
        p_client = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        p_client.text = f"Client: {client_name}"
        p_client.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run_client = p_client.runs[0] if p_client.runs else p_client.add_run()
        run_client.font.size = Pt(12)

        p_date = header.add_paragraph()
        p_date.text = f"Submission Date: {submission_date}"
        p_date.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        run_date = p_date.runs[0]
        run_date.font.size = Pt(12)

        # Process template sections
        for section in template_config['sections']:
            if section['type'] == 'title':
                self._add_title_page(doc, section['content'], client_name)
            elif section['type'] == 'section':
                doc.add_page_break()  # Add page break before Personal Circumstances
                self._add_section(doc, section['name'], section)

        # Save to BytesIO
        f = BytesIO()
        doc.save(f)
        f.seek(0)
        return f

    def _add_title_page(self, doc, content, client_name):
        """Add a title page to the document"""
        # Add court name
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p.add_run(content['court'])
        run.bold = True
        run.font.size = Pt(14)

        # Add location
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p.add_run(content['location'])
        run.bold = True
        run.font.size = Pt(14)

        # Add parties
        for party in content['parties']:
            p = doc.add_paragraph()
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            run = p.add_run(party.format(client_name=client_name))
            run.bold = True
            run.font.size = Pt(12)

    def _add_section(self, doc, section_name, subsections_or_config):
        """Add a section with subsections and their fields"""
        doc.add_heading(section_name, level=1)
        
        # Initialize answer counter
        answer_number = 1
        
        # Determine if we should use form sections or template-defined subsections
        if isinstance(subsections_or_config, dict) and subsections_or_config.get('use_form_sections'):
            # Use sections from the form
            for section in self.sections:
                section_name = section.get('name', '')
                if section_name:
                    # Find questions for this section
                    section_questions = [
                        q for q in self.questions.values()
                        if q.section_id == section.get('id') and self.answers_by_question.get(q.pk)
                    ]
                    
                    if section_questions:
                        doc.add_heading(section_name, level=2)
                        for q in section_questions:                        answer_obj = Answer.objects.filter(submission=self.submission, question=q).first()
                        if answer_obj and str(answer_obj.value).strip():
                            p = doc.add_paragraph()
                            p.add_run(f"{answer_number}. ").bold = True
                            p.add_run(f"{q.text}: ").bold = True
                            p.add_run(str(answer_obj.get_formatted_value()))
                            answer_number += 1
        else:
            # Use template-defined subsections (for bail application or other templates)
            for subsection in subsections_or_config:
                subsection_lower = subsection.lower()
                matching_questions = [
                    q for q in self.questions.values()
                    if subsection_lower in q.text.lower()
                    and self.answers_by_question.get(q.pk)
                ]
                
                if matching_questions:
                    doc.add_heading(subsection, level=2)
                    for q in matching_questions:
                        answer_obj = Answer.objects.filter(submission=self.submission, question=q).first()
                        if answer_obj and str(answer_obj.value).strip():
                            p = doc.add_paragraph()
                            p.add_run(f"{answer_number}. ").bold = True
                            p.add_run(f"{q.text}: ").bold = True
                            p.add_run(str(answer_obj.get_formatted_value()))
                            answer_number += 1