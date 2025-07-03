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

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Python dependencies from pyproject.toml
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv add gunicorn && uv sync

# Copy the backend application code into the container
COPY backend/ .

# Copy the built frontend assets from the frontend-builder stage
# Your Django `STATICFILES_DIRS` setting should be configured to include this `/app/static` directory.
COPY --from=frontend-builder /app/frontend/dist /app/static

# Expose port 8000 to allow communication to the Gunicorn server
EXPOSE 8000

# Run the application using Gunicorn
# This command assumes your Django project's WSGI file is located at `form_generator.wsgi`.
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "form_generator.wsgi:application"]
 