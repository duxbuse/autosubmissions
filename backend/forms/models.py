# forms/models.py
from django.db import models

class Form(models.Model):
    """
    Represents a form type, e.g., 'Bail Hearing'.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    form = models.ForeignKey(Form, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=1024)
    question_type = models.CharField(max_length=10, choices=QuestionType.choices)
    order = models.PositiveIntegerField()
    output_template = models.TextField(
        blank=True,
        help_text="Sample submission text. Use {{answer}} to insert the user's answer."
    )
    hidden = models.BooleanField(default=False)
    any_option_triggers_question = models.ForeignKey(
        'self',
        related_name='triggered_by_any_option',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If any option is selected, this question will be shown (for dropdowns)."
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
    triggers_question = models.ForeignKey(
        Question,
        related_name='triggered_by_options',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If this option is selected, this question will be shown."
    )

    def __str__(self):
        return self.text

class Submission(models.Model):
    """
    A single, completed form submission by a user.
    """
    form = models.ForeignKey(Form, on_delete=models.PROTECT)
    client_name = models.CharField(max_length=255)
    submission_date = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    """
    A user's answer to a specific question in a submission.
    """
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    value = models.TextField() # Stores text, or a JSON list of selected option IDs

