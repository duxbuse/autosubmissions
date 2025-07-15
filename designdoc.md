# Design & Architecture: Dynamic Form & Document Generator

## 1. Introduction

This document outlines the design and architecture for a web application that allows users to build dynamic forms and generate formatted Word documents from form submissions.

The primary goal is to streamline the process of data collection and document creation for structured procedures, such as legal filings (e.g., "Bail Hearing"). The system is composed of two main user-facing components: a **Form Builder** for creating form templates and a **Form Submitter** for filling out these forms to generate a final document.

## 2. Key Features

*   **Home Page**: A landing page that lists all available form types for submission.
*   **Dynamic Form Builder**: An interface, similar to Google Forms, for creating and editing form types.
    *   Supports question types: Text, Multiple Choice, Checkboxes, and Dropdown.
    *   Allows for conditional logic where answering a question can reveal subsequent questions (triggered/hidden questions are visually connected in the submitter UI).
    *   For each question, the builder can define a corresponding "sample submission" text snippet. This snippet acts as a template for the final document.
*   **Form Submission**: A user-friendly interface for filling out a form based on a pre-defined type.
    *   Triggered (hidden) questions appear as smaller, right-aligned boxes visually connected to the triggering question.
    *   All form tiles and question blocks use a modern, professional, and visually consistent theme.
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

The backend is a Django project containing several focused apps, while the frontend is a standalone Vue.js application.

### 4.1. Project File Structure

The project is organized into a separate backend and frontend.

```
autosubmissions/
├── backend/
│   ├── manage.py
│   ├── form_generator/  # Core Django project settings
│   ├── forms/           # App for core models (Form, Question, etc.)
│   ├── form_json/       # App to generate form structures as JSON for the frontend
│   └── submission_json/ # App to handle incoming JSON submissions
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/             # Vue.js application source
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
    template_config = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON configuration for document template structure and formatting"
    )

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

This logic is encapsulated in the `DocGenerator` class which uses a template-based approach for document generation.

#### 4.4.1 Template Configuration System

The system uses a flexible JSON-based template configuration system with two levels:

1. **Default Templates**: Stored in the `DocGenerator` class as `DEFAULT_TEMPLATES`
   * Provides base templates for common form types (plea_of_guilty, bail_application)
   * Defines standard section types and formatting
   * Acts as a fallback when no custom template is specified

2. **Custom Templates**: Stored in the Form model's `template_config` field
   * Allows per-form customization of document structure
   * Can override or extend default templates
   * Provides flexibility for special case documents

**Template Structure Example:**

```json
{
    "title": "OUTLINE OF SUBMISSIONS FOR PLEA HEARING",
    "sections": [
        {
            "name": "title_page",
            "type": "title",
            "content": {
                "court": "IN THE MAGISTRATES' COURT",
                "location": "AT MELBOURNE",
                "parties": ["VICTORIA POLICE", "and", "{client_name}"]
            }
        },
        {
            "name": "chronology",
            "type": "table",
            "headers": ["date", "event"],
            "question_key": "chronology"
        }
    ]
}
```

#### 4.4.2 Section Types

The template system supports various section types, each with specific formatting and behavior:

1. **Title (`title`)**  
   * Centered text with specific spacing
   * Support for dynamic content replacement
   * Consistent court document formatting

2. **Text (`text`)**  
   * Basic paragraphs with optional headings
   * Support for default text values
   * Dynamic content from form answers

3. **Table (`table`)**  
   * Configurable headers
   * Auto-formatting for consistent appearance
   * Optional total row calculations
   * Summary text generation

4. **List (`list`)**  
   * Bullet points or numbered lists
   * Configurable headings
   * Dynamic content from form answers

5. **Composite (`composite`)**  
   * Complex sections with multiple parts
   * Introduction text support
   * Sub-section handling

6. **Sections (`sections`)**  
   * Grouped content with titles
   * Multiple subsection support
   * Flexible content organization

7. **Details (`details`)**  
   * Form field layouts
   * Standard formatting for document metadata
   * Support for firm details and dates

8. **Signature (`signature`)**  
   * Standard signature block formatting
   * Date fields
   * Consistent spacing

#### 4.4.3 Document Generation Process

1. **Template Selection**
   * Check Form's `template_config`
   * Fall back to `DEFAULT_TEMPLATES` if not specified
   * Validate template structure

2. **Section Processing**
   * Iterate through template sections
   * Call appropriate section handler methods
   * Apply section-specific formatting

3. **Data Mapping**
   * Map submission answers to template placeholders
   * Handle dynamic content replacement
   * Apply consistent formatting

4. **Document Assembly**
   * Build document section by section
   * Maintain consistent styling
   * Handle special formatting requirements

5. **Output Generation**
   * Create final document in memory
   * Apply any global formatting
   * Return as BytesIO stream

### 4.5 API Endpoints for Template Management

Additional endpoints to support template configuration:

* `GET /api/forms/<id>/template/`: Retrieve the current template configuration
* `PUT /api/forms/<id>/template/`: Update the template configuration
* `DELETE /api/forms/<id>/template/`: Reset to default template

## 5. Frontend Design (Vue.js)

The frontend will be a Single Page Application (SPA) that communicates with the backend via the REST API.

### 5.1. Component Breakdown

*   **`App`**: The root component, handling routing.
*   **`HomePage`**: Fetches and displays a list of forms from `/api/forms/`. Each item links to `/form/submit/<id>`.
*   **`FormBuilder` (`/form/build/<id>`)**:
    *   Manages the state of the form being built (questions, options, conditional logic).
    *   Fetches initial form data from `/api/forms/<id>/`.
    *   Provides a UI to add, edit, reorder, and delete questions.
    *   For each question, it includes input fields for `text`, `question_type` (Text, Multiple Choice, Checkboxes, Dropdown), and the `output_template`.
    *   For each option, it includes an input to select a `triggers_question` to establish conditional logic.
    *   All form tiles are perfect squares, centered, and visually consistent.
    *   Saves changes via `PUT` requests to `/api/forms/<id>/`.
*   **`FormSubmitter` (`/form/submit/<id>`)**:
    *   Fetches the form structure from `/api/forms/<id>/`.
    *   Renders the questions dynamically.
    *   Manages the visibility of conditional questions based on user selections in real-time.
    *   Triggered (hidden) questions are rendered as smaller, right-aligned boxes within the same question block, visually connected to the triggering question.
    *   All question blocks and form elements use a modern, professional, and visually consistent theme.
    *   On submit, it packages the answers into a JSON object and `POST`s it to `/api/submissions/`.
    *   After a successful submission, it could redirect the user to a page with a link to download the document (`/api/submissions/<new_id>/generate-doc/`).

### 5.2. State Management

*   State is managed locally within each component (no global state management library is currently used, but Pinia is recommended for future scalability).
*   All styles are centralized in a global `main.css` file for a consistent, modern look and easy theming.
