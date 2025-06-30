# Design & Architecture: Dynamic Form & Document Generator

## 1. Introduction

This document outlines the design and architecture for a web application that allows users to build dynamic forms and generate formatted Word documents from form submissions.

The primary goal is to streamline the process of data collection and document creation for structured procedures, such as legal filings (e.g., "Bail Hearing"). The system is composed of two main user-facing components: a **Form Builder** for creating form templates and a **Form Submitter** for filling out these forms to generate a final document.

## 2. Key Features

*   **Home Page**: A landing page that lists all available form types for submission.
*   **Dynamic Form Builder**: An interface, similar to Google Forms, for creating and editing form types.
    *   Supports various question types (text, multiple choice, etc.).
    *   Allows for conditional logic where answering a question can reveal subsequent questions.
    *   For each question or section, the builder can define a corresponding "sample submission" text snippet. This snippet acts as a template for the final document.
*   **Form Submission**: A user-friendly interface for filling out a form based on a pre-defined type.
*   **Document Generation**: On submission, the system compiles the answers. It uses the "sample submission" snippets associated with each answered question, populates them with the user's data, and generates a cohesive, formatted `.docx` Word document.

## 3. System Architecture

We will adopt a **Monolithic Architecture** with a decoupled frontend. This approach is well-suited for this project's scope, providing a strong, unified backend while allowing for a modern, dynamic user experience on the frontend.

### 3.1. Technology Stack

*   **Backend**: Python with the **Django** framework.
*   **API**: Django REST Framework (DRF) to create a RESTful API.
*   **Database**: **PostgreSQL** for its robustness and rich feature set.
*   **Frontend**: The **Vue.js** framework.
*   **Document Generation**: The `python-docx` library.
*   **Web Server**: Gunicorn.
*   **Reverse Proxy**: Nginx.

### 3.2. High-Level Diagram

```
+----------------+      +----------------------+      +--------------------+
|                |      |                      |      |                    |
|   User Browser |----->|     Nginx            |----->|   Gunicorn /       |
| (Vue App)      |      | (Reverse Proxy /     |      |   Django App       |
|                |      |  Serving Static)     |      | (Python Backend)   |
+----------------+      +----------------------+      +----------+---------+
                                                                 |
                                                                 |
                                                      +----------v---------+
                                                      |                    |
                                                      |   PostgreSQL DB    |
                                                      |                    |
                                                      +--------------------+
```

## 4. Backend Design (Python / Django)

The backend will be a single Django project containing several focused apps.

### 4.1. Django App Structure

```
form_generator/
├── form_generator/  # Core project settings
│   ├── settings.py
│   └── urls.py
├── forms/           # The core application for forms and submissions
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── users/           # For user authentication and management (optional but recommended)
│   └── ...
└── manage.py
```

### 4.2. Database Models (`forms/models.py`)

The database schema is central to the application.

```python
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
        PARAGRAPH = 'PARAGRAPH', 'Paragraph'
        MULTIPLE_CHOICE = 'MC', 'Multiple Choice'
        CHECKBOXES = 'CHECK', 'Checkboxes'
        DROPDOWN = 'DROP', 'Dropdown'

    form = models.ForeignKey(Form, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=1024)
    question_type = models.CharField(max_length=10, choices=QuestionType.choices)
    order = models.PositiveIntegerField()
    # This is the template for the final document output for this question
    output_template = models.TextField(
        blank=True,
        help_text="Sample submission text. Use {{answer}} to insert the user's answer."
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
    # This links an option to a question that should be shown if this option is selected
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
    submitted_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    """
    A user's answer to a specific question in a submission.
    """
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    value = models.TextField() # Stores text, or a JSON list of selected option IDs

```

### 4.3. API Endpoints (DRF)

We will expose RESTful endpoints for the frontend to consume.

*   `GET /api/forms/`: List all available `Form` types.
*   `POST /api/forms/`: Create a new `Form`.
*   `GET /api/forms/<id>/`: Retrieve the full structure of a single `Form`, including its `Questions` and `Options`. This is used by both the builder and the submission page.
*   `PUT /api/forms/<id>/`: Update a `Form` (e.g., changing its name or questions).
*   `POST /api/submissions/`: Submit a new `Submission` with all its `Answers`.
*   `GET /api/submissions/<id>/generate-doc/`: The key endpoint to trigger the `.docx` generation for a completed submission.

### 4.4. Document Generation Logic

This logic will reside in a view connected to the `generate-doc` endpoint.

1.  Receive a `submission_id`.
2.  Fetch the `Submission` object and its related `Answer` set.
3.  Initialize a new document using `python-docx`.
4.  Iterate through the `Answers` in the correct question order.
5.  For each `Answer`:
    *   Get the corresponding `Question` and its `output_template`.
    *   If the template is not empty, use Python's f-strings or `str.replace()` to substitute the placeholder (e.g., `{{answer}}`) with the `Answer.value`.
    *   Add the resulting text to the document as a new paragraph, applying any required styling (e.g., bolding, headings).
6.  Create an in-memory byte stream of the `.docx` file.
7.  Return an `HttpResponse` with the correct `Content-Type` (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) and `Content-Disposition` headers to trigger a file download in the browser.

## 5. Frontend Design (Vue.js)

The frontend will be a Single Page Application (SPA) that communicates with the backend via the REST API.

### 5.1. Component Breakdown

*   **`App`**: The root component, handling routing.
*   **`HomePage`**: Fetches and displays a list of forms from `/api/forms/`. Each item links to `/form/submit/<id>`.
*   **`FormBuilder` (`/form/build/<id>`)**:
    *   Manages the state of the form being built (questions, options, conditional logic).
    *   Fetches initial form data from `/api/forms/<id>/`.
    *   Provides a UI to add, edit, reorder, and delete questions.
    *   For each question, it includes input fields for `text`, `question_type`, and the `output_template`.
    *   For each option, it includes an input to select a `triggers_question` to establish conditional logic.
    *   Saves changes via `PUT` requests to `/api/forms/<id>/`.
*   **`FormSubmitter` (`/form/submit/<id>`)**:
    *   Fetches the form structure from `/api/forms/<id>/`.
    *   Renders the questions dynamically.
    *   Manages the visibility of conditional questions based on user selections in real-time.
    *   On submit, it packages the answers into a JSON object and `POST`s it to `/api/submissions/`.
    *   After a successful submission, it could redirect the user to a page with a link to download the document (`/api/submissions/<new_id>/generate-doc/`).

### 5.2. State Management

A state management library (**Pinia for Vue**) is highly recommended for the `FormBuilder` and `FormSubmitter` components. It will simplify handling the complex and interconnected state of questions, answers, and conditional visibility.
