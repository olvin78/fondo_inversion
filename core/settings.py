from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --------------------------------------------------
# BASE DIR
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# VARIABLES DE ENTORNO
# --------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "clave-insegura-de-django")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

# --------------------------------------------------
# APPS INSTALADAS
# --------------------------------------------------
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Allauth
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # Tus apps
    "applications.accounts",
    "applications.home",
    "applications.investors",
    "applications.products",
    "applications.portfolios",
    "applications.transactions",
    "applications.funds",
]

SITE_ID = 1

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Allauth
    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------
# URL PRINCIPAL
# --------------------------------------------------
ROOT_URLCONF = "core.urls"

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates"  # Carpeta global de templates
        ],
        "APP_DIRS": True,  # Buscar templates dentro de cada app
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # NECESARIO PARA ALLAUTH
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------
# WSGI
# --------------------------------------------------
WSGI_APPLICATION = "core.wsgi.application"

# --------------------------------------------------
# BASE DE DATOS
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --------------------------------------------------
# VALIDADORES
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    { "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator" },
    { "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8} },
    { "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator" },
    { "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator" },
]

# --------------------------------------------------
# IDIOMA Y ZONA HORARIA
# --------------------------------------------------
LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"

USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# ARCHIVOS ESTÁTICOS
# --------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static"
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# --------------------------------------------------
# MEDIA
# --------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# AUTENTICACIÓN (ALLAUTH)
# --------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Login normal
    "allauth.account.auth_backends.AuthenticationBackend",  # Login con Google
]

LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/"

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "none"

# Necesario para que Google funcione en local
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"

# Configuración de Google (lee variables de .env)
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_SECRET_KEY"),
            "key": "",
        }
    }
}

# --------------------------------------------------
# CONFIG FINAL
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

