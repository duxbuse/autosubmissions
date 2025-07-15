from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import parse_xml
from io import BytesIO
from datetime import datetime
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
        
        # Set up the document
        section = doc.sections[0]
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        
        # Set up default paragraph style
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        style.paragraph_format.space_after = Pt(0)  # No extra space after paragraphs by default
        
        # No header section needed

        # Get client name for the document
        client_name = self.submission.client_name or 'client'

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
        """Add a title page to the document following court format"""
        # Set up styles for left-aligned text
        style = doc.styles.add_style('Court Header Left', WD_STYLE_TYPE.PARAGRAPH)
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        style.paragraph_format.space_after = Pt(0)

        # Add court name and location in top left
        p = doc.add_paragraph(style='Court Header Left')
        p.add_run(content['court'])
        
        p = doc.add_paragraph(style='Court Header Left')
        p.add_run(content['location'])

        # Set up center style for parties
        style = doc.styles.add_style('Court Header Center', WD_STYLE_TYPE.PARAGRAPH)
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        style.font.bold = True
        style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        style.paragraph_format.space_after = Pt(6)

        # Add spacing before parties
        doc.add_paragraph()
        doc.add_paragraph()
        
        # Center align the parties
        p = doc.add_paragraph(style='Court Header Center')
        victoria_police = p.add_run("VICTORIA POLICE")
        
        p = doc.add_paragraph(style='Court Header Center')
        p.add_run("and")

        # Add client name (surname only)
        p = doc.add_paragraph(style='Court Header Center')
        # Get just the surname (last word in the name)
        name_parts = client_name.split()
        surname = name_parts[-1]  # Take the last part as surname
        p.add_run(surname.upper())

        # Add spacing before title
        doc.add_paragraph()
        doc.add_paragraph()

        # Set up centered style for title
        if 'Court Header Center Bold' not in doc.styles:
            style = doc.styles.add_style('Court Header Center Bold', WD_STYLE_TYPE.PARAGRAPH)
            style.font.name = 'Times New Roman'
            style.font.size = Pt(12)
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            style.paragraph_format.space_after = Pt(12)

        # Add the underlined title
        p = doc.add_paragraph(style='Court Header Center Bold')
        title_run = p.add_run("OUTLINE OF SUBMISSIONS FOR PLEA HEARING")
        title_run.bold = True
        title_run.underline = True
        
        # Add the information table
        doc.add_paragraph()  # Space before table
        table = doc.add_table(rows=4, cols=2)
        table.style = None  # Remove default table style
        table.autofit = False
        table.allow_autofit = False
        
        # Set full width table with right-aligned second column
        section = doc.sections[0]
        available_width = section.page_width - section.left_margin - section.right_margin
        # Convert to twips (twentieth of a point)
        total_width = int(available_width * 1440 / Inches(1))
        col1_width = int(total_width * 0.7)  # 70% for first column
        col2_width = int(total_width * 0.3)  # 30% for second column
        
        # Set column widths
        for cell in table.columns[0].cells:
            cell._tc.tcPr.append(parse_xml(f'<w:tcW xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:w="{col1_width}" w:type="dxa"/>'))
        for cell in table.columns[1].cells:
            cell._tc.tcPr.append(parse_xml(f'<w:tcW xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:w="{col2_width}" w:type="dxa"/>'))

        # Set table properties and borders
        
        # Create table properties
        tblPr = parse_xml(r'''<w:tblPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:tblBorders>
                <w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>
                <w:left w:val="none"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>
                <w:right w:val="none"/>
                <w:insideH w:val="none"/>
                <w:insideV w:val="dashed" w:sz="4" w:space="0" w:color="auto"/>
            </w:tblBorders>
        </w:tblPr>''')
        
        # Remove any existing table properties
        for element in table._element.findall('.//w:tblPr', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
            element.getparent().remove(element)
        
        # Add the new table properties
        table._element.insert(0, tblPr)

        # Fill table
        table.cell(0, 0).text = "Date of Document:"
        table.cell(0, 1).text = datetime.now().strftime("%d %B %Y")
        table.cell(1, 0).text = "Filed on behalf of:"
        table.cell(1, 1).text = "The Accused"
        table.cell(2, 0).text = "Prepared by:"
        table.cell(2, 1).text = "Solicitors code: 113 758"
        table.cell(3, 0).text = "James Dowsley & Associates"
        table.cell(3, 1).text = "Telephone: 9781 4900"

        # Format table text and align second column to right
        for row in table.rows:
            for i, cell in enumerate(row.cells):
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    if i == 1:  # Second column
                        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    for run in paragraph.runs:
                        run.font.name = 'Calibri'
                        run.font.size = Pt(11)

    def _add_section(self, doc, section_name, subsections_or_config):
        """Add a section with subsections and their fields"""
        # Create section heading style
        if 'Section Heading' not in doc.styles:
            style = doc.styles.add_style('Section Heading', WD_STYLE_TYPE.PARAGRAPH)
            style.font.name = 'Times New Roman'
            style.font.size = Pt(12)
            style.font.bold = True
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(6)
            style.paragraph_format.keep_with_next = True

        # Create italic subheading style
        if 'Italic Subheading' not in doc.styles:
            style = doc.styles.add_style('Italic Subheading', WD_STYLE_TYPE.PARAGRAPH)
            style.font.name = 'Times New Roman'
            style.font.size = Pt(12)
            style.font.italic = True
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(6)
            style.paragraph_format.left_indent = Inches(0)

        # Create answer text style
        if 'Answer Text' not in doc.styles:
            style = doc.styles.add_style('Answer Text', WD_STYLE_TYPE.PARAGRAPH)
            style.font.name = 'Times New Roman'
            style.font.size = Pt(12)
            style.paragraph_format.space_after = Pt(6)
            style.paragraph_format.left_indent = Inches(0.5)
            style.paragraph_format.first_line_indent = Inches(-0.25)  # Hanging indent for numbers
            style.paragraph_format.line_spacing = 1.0

        # Add the section heading
        p = doc.add_paragraph(style='Section Heading')
        p.add_run(section_name.upper())  # Make section heading uppercase
        
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
                        # All section headings except the main "PERSONAL CIRCUMSTANCES" should be italic
                        if section_name.lower() != "personal circumstances":
                            p = doc.add_paragraph(style='Italic Subheading')
                            p.add_run(section_name.lower())  # Use lowercase for subheadings
                        
                        for q in section_questions:
                            answer_obj = Answer.objects.filter(submission=self.submission, question=q).first()
                            if answer_obj and str(answer_obj.value).strip():
                                p = doc.add_paragraph(style='Answer Text')
                                # Add the number and question text together with the answer
                                answer_text = f"{answer_number}. {q.text} {str(answer_obj.get_formatted_value())}"
                                p.add_run(answer_text)
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
                    # All subsection headings should be italic except main sections
                    if subsection.lower() != "personal circumstances":
                        p = doc.add_paragraph(style='Italic Subheading')
                        p.add_run(subsection.lower())  # Use lowercase for subheadings
                    else:
                        p = doc.add_paragraph(style='Section Heading')
                        p.add_run(subsection.upper())
                    
                    for q in matching_questions:
                        answer_obj = Answer.objects.filter(submission=self.submission, question=q).first()
                        if answer_obj and str(answer_obj.value).strip():
                            p = doc.add_paragraph(style='Answer Text')
                            # Add the number and question text together with the answer
                            answer_text = f"{answer_number}. {q.text} {str(answer_obj.get_formatted_value())}"
                            p.add_run(answer_text)
                            answer_number += 1