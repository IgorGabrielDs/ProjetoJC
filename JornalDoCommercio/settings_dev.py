from .settings import * 
import os

DEBUG = True

if not SECRET_KEY:
    SECRET_KEY = 'django-insecure-dev-key-for-testing-only'

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "testserver", 
    "jcproject.azurewebsites.net",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@jc.local")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "noticias" / "static"]

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.azurewebsites.net",
]