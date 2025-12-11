from pathlib import Path
import os
from dotenv import load_dotenv 

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv("WEBSITE_HOSTNAME") is None

ALLOWED_HOSTS = ['jcproject.azurewebsites.net', '127.0.0.1', 'localhost']

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "caca_links",
    'django_apscheduler',
    "sudoku",
    'noticias.apps.NoticiasConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'JornalDoCommercio.urls'

CSRF_TRUSTED_ORIGINS = [
    "https://jcproject.azurewebsites.net",
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'JornalDoCommercio.wsgi.application'

APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"

APSCHEDULER_RUN_MIGRATIONS = True



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DBNAME"),
        "USER": os.getenv("DBUSER"),
        "PASSWORD": os.getenv("DBPASSWORD"),
        "HOST": os.getenv("DBHOST"),
        "PORT": os.getenv("DBPORT"),
        "OPTIONS": {
            "sslmode": os.getenv("DBSSLMODE"),
        },
    }
} 
        

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Recife'

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "noticias" / "static",
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

os.makedirs(MEDIA_ROOT, exist_ok=True)

AUTHENTICATION_BACKENDS = [
    "noticias.backends.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"