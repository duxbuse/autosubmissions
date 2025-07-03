# syntax=docker.io/docker/dockerfile:1.7-labs
# Dockerfile for the Django + Vue.js application

# --- Stage 1: Build Vue.js Frontend ---
FROM node:18-alpine AS frontend-builder

# Set working directory for the frontend
WORKDIR /app/frontend

# Copy package files and install dependencies
# Using `package-lock.json` ensures reproducible builds
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --include=dev

# Copy the rest of the frontend source code
COPY frontend/ ./

# Build the static assets for the frontend
RUN npm run build

# --- Stage 2: Build Python Backend ---
FROM python:3.13-slim

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by psycopg2 (for PostgreSQL)
# Updating package lists and installing dependencies in one RUN command reduces image layers.
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && apt-get clean

# Install Python dependencies from pyproject.toml
# For production, it's often better to use a requirements.txt file,
# but this works for the current project structure.
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir django djangorestframework django-cors-headers psycopg2-binary python-docx gunicorn

# Copy the backend application code into the container
COPY backend/ .

# Copy the built frontend assets from the frontend-builder stage
# Your Django `STATICFILES_DIRS` setting should be configured to include this `/app/static` directory.
COPY --from=frontend-builder /app/frontend/dist /app/static/

# Expose port 8000 to allow communication to the Gunicorn server
EXPOSE 8000

# Run the application using Gunicorn
# This command assumes your Django project's WSGI file is located at `form_generator.wsgi`.
# You may need to adjust this based on your project's name.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "form_generator.wsgi:application"]
