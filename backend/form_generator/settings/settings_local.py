from .settings_base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
ALLOWED_HOSTS = []

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173", # vite when running locally
]