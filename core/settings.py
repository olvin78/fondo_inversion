from pathlib import Path
import os
from dotenv import load_dotenv

# --------------------------------------------------
# CARGA DE VARIABLES .ENV
# --------------------------------------------------
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
# INSTALLED APPS
# --------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django.contrib.sites",

    # allauth-ui primero (sobrescribe plantillas)
    "allauth_ui",

    # allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # dependencias de allauth-ui
    "widget_tweaks",
    "slippers",

    # Tus apps
    "applications.accounts",
    "applications.home",
    "applications.investors",
    "applications.products",
    "applications.portfolios",
    "applications.transactions",
    "applications.funds",
    "applications.client",
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

    # Middleware de Allauth
    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------
# ROOT URL
# --------------------------------------------------
ROOT_URLCONF = "core.urls"

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates"
        ],
        "APP_DIRS": True,
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
# DATABASE
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --------------------------------------------------
# PASSWORD VALIDATORS
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
    "allauth.account.auth_backends.AuthenticationBackend",  # Login email + social
]

# Redirecciones tras login/logout
LOGIN_REDIRECT_URL = "/client/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Configuración del sistema de cuentas
#ACCOUNT_EMAIL_REQUIRED = True
#ACCOUNT_USERNAME_REQUIRED = False
#ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# django-allauth (configuración moderna)
ACCOUNT_LOGIN_METHODS = {"email"}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"



ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]
AUTH_USER_MODEL = "auth.User"  # (si no usas uno custom)


# Forzar protocolo http en desarrollo (Google)
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"

# --------------------------------------------------
# CONFIGURACIÓN GOOGLE LOGIN
# --------------------------------------------------
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_SECRET_KEY"),
            "key": "",
        },
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

# --------------------------------------------------
# ALLAUTH UI: TEMA VISUAL
# --------------------------------------------------
ALLAUTH_UI_THEME = "corporate"  # Puedes usar: light, dark, minimal, corporate

# --------------------------------------------------
# CONFIG FINAL
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
