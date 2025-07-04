from .settings_base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "autosubmissions",
        "USER": "autosubmissions",
        "PASSWORD": "autosubmissions",
        "HOST": "db",
        "PORT": "5432",
    }
}

ALLOWED_HOSTS = ["*", "localhost"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080", # nginx when running in compose
]