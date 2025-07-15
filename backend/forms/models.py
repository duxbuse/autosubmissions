# forms/models.py
from django.db import models


class Form(models.Model):
    """
    Represents a form type, e.g., 'Bail Hearing'.
    """
    class TemplateType(models.TextChoices):
        PLEA_OF_GUILTY = 'plea_of_guilty', 'Plea of Guilty'
        BAIL_APPLICATION = 'bail_application', 'Bail Application'

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # --- Template configuration ---
    template_type = models.CharField(
        max_length=50,
        choices=TemplateType.choices,
        default=TemplateType.PLEA_OF_GUILTY,
        help_text="The type of document template to use for this form"
    )
    template_config = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Configuration for document generation, including sections to include, their order, and formatting."
    )
    # --- Section support ---
    sections = models.JSONField(null=True, blank=True, help_text="List of sections for this form, as an array of objects with id and name.")

    def __str__(self):
        return self.name

class Question(models.Model):
    """
    A single question within a Form.
    """
    class QuestionType(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        MULTIPLE_CHOICE = 'MC', 'Multiple Choice'
        CHECKBOXES = 'CHECK', 'Checkboxes'
        DROPDOWN = 'DROP', 'Dropdown'
        DATE = 'DATE', 'Date'

    form = models.ForeignKey(Form, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=1024)
    question_type = models.CharField(max_length=10, choices=QuestionType.choices)
    order = models.PositiveIntegerField()
    output_template = models.TextField(
        blank=True,
        help_text="Sample submission text. Use {{answer}} to insert the user's answer."
    )
    hidden = models.BooleanField(default=False)
    # --- Section support ---
    section_id = models.IntegerField(null=True, blank=True, help_text="Section ID this question belongs to (from form.sections array, not a FK)")
    # Allow any question to trigger other questions (not just options)
    triggers_question = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='triggered_by_question',
        blank=True,
        help_text="If this question is answered, these questions will be shown."
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.form.name} - Q{self.order}: {self.text[:50]}"

class Option(models.Model):
    """
    An option for a multiple-choice, checkbox, or dropdown question.
    """
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    triggers_question = models.ManyToManyField(
        'Question',
        related_name='triggered_by_options',
        blank=True,
        help_text="If this option is selected, these questions will be shown."
    )

    def __str__(self):
        return self.text

class Submission(models.Model):
    """
    A single, completed form submission by a user.
    """
    form = models.ForeignKey(Form, on_delete=models.PROTECT)
    client_honorific = models.CharField(max_length=10, blank=True)
    client_first_name = models.CharField(max_length=255)
    client_surname = models.CharField(max_length=255)
    submission_date = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    @property
    def client_name(self):
        """
        Returns the full name of the client, maintaining compatibility with existing code.
        """
        parts = []
        if self.client_honorific:
            parts.append(self.client_honorific)
        parts.extend([self.client_first_name, self.client_surname])
        return ' '.join(parts)

class Answer(models.Model):
    """
    A user's answer to a specific question in a submission.
    """
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True)
    value = models.TextField() # Stores text, or a JSON list of selected option IDs

    def get_formatted_value(self):
        """
        Returns the answer value with template variables replaced.
        Supports {{answer}} and {{name}} variables.
        """
        if not self.question or not self.question.output_template:
            return self.value

        # Get the formatted text with {{answer}} replaced
        text = self.question.output_template.replace('{{answer}}', self.value)
        
        # Replace {{name}} with honorific + surname if present
        if '{{name}}' in text and self.submission:
            name_parts = []
            if self.submission.client_honorific:
                name_parts.append(self.submission.client_honorific)
            if self.submission.client_surname:
                name_parts.append(self.submission.client_surname)
            name = ' '.join(name_parts)
            text = text.replace('{{name}}', name)
            
        return text

