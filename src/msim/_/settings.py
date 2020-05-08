import json
import os
import string

from django.urls import reverse_lazy


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
placeholder_secret_key = "kick me"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", placeholder_secret_key)

# SECURITY WARNING: don"t run with debug turned on in production!
DEBUG = json.loads(os.getenv("DJANGO_DEBUG", "false"))

if not DEBUG and SECRET_KEY == placeholder_secret_key:
    raise ValueError("you must set `DJANGO_SECRET_KEY` outside of local dev")

ALLOWED_HOSTS = json.loads(os.getenv("DJANGO_ALLOWED_HOSTS", "[]"))


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "mortgages",
    "registration",
    "website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "_.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "_.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
databases_template = string.Template(os.getenv(
    "DJANGO_DATABASES",
    json.dumps({
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "${BASE_DIR}/db.sqlite3",
        },
    }),
))
DATABASES = json.loads(databases_template.substitute({"BASE_DIR": BASE_DIR}))


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = json.loads(os.getenv(
    "DJANGO_AUTH_PASSWORD_VALIDATORS",
    "[]",
))


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
LANGUAGE_CODE = os.getenv("DJANGO_LANGUAGE_CODE", "en-gb")

TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_URL = "/static/"

LOGIN_REDIRECT_URL = reverse_lazy("mortgages:list")
LOGOUT_REDIRECT_URL = "/"
