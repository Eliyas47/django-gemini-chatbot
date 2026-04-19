# backend/settings.py
from pathlib import Path
from importlib.util import find_spec
import os
from dotenv import load_dotenv
import dj_database_url

# Avoid importing optional dependency directly to keep Pylance happy
# when whitenoise is not installed in the active environment.
WHITE_NOISE_INSTALLED = find_spec("whitenoise") is not None

# -------------------------------
# BASE DIRECTORY
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------
# LOAD .env
# -------------------------------
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    print(f"⚠️ WARNING: .env file not found at {dotenv_path}, GEMINI_API_KEY may be missing")

# -------------------------------
# SECURITY
# -------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-for-dev")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = ["*"]

# -------------------------------
# APPLICATIONS
# -------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'chatbot',
    'corsheaders',
    'drf_yasg',
]

# -------------------------------
# MIDDLEWARE
# -------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if WHITE_NOISE_INSTALLED:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# -------------------------------
# URLS & TEMPLATES
# -------------------------------
ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

# -------------------------------
# PASSWORD VALIDATION
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------
# INTERNATIONALIZATION
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------------
# STATIC FILES
# -------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# DEFAULT AUTO FIELD
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------
# DJANGO REST FRAMEWORK
# -------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'chatbot.exceptions.api_exception_handler',
}

# -------------------------------
# GEMINI API KEY
# -------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not set. Using TEST KEY for development.")
    GEMINI_API_KEY = "TEST_KEY"

# -------------------------------
# MEDIA / CORS / DATABASE
# -------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
CORS_ALLOW_ALL_ORIGINS = True

DATABASE_URL = os.getenv("DATABASE_URL")

# Never expose Django debug pages in production unless explicitly forced.
is_hosted_runtime = bool(os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_URL"))
if (DATABASE_URL or is_hosted_runtime) and os.getenv("FORCE_DEBUG_IN_PROD", "False").lower() != "true":
    DEBUG = False

# Render Postgres commonly requires SSL. Keep local sqlite unaffected and allow
# overriding through DB_SSL_REQUIRED when needed.
db_ssl_required = os.getenv("DB_SSL_REQUIRED")
if db_ssl_required is None:
    db_ssl_required = bool(DATABASE_URL)
else:
    db_ssl_required = db_ssl_required.lower() == "true"

if DATABASE_URL:
    db_conn_max_age = int(os.getenv("DB_CONN_MAX_AGE", "0"))
    database_config = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=db_conn_max_age,
        ssl_require=db_ssl_required,
    )
    database_config["CONN_HEALTH_CHECKS"] = True
    options = database_config.setdefault("OPTIONS", {})
    if db_ssl_required:
        options.setdefault("sslmode", "require")
    # Improve resiliency for intermittent network hiccups.
    options.setdefault("connect_timeout", 10)
    options.setdefault("keepalives", 1)
    options.setdefault("keepalives_idle", 30)
    options.setdefault("keepalives_interval", 10)
    options.setdefault("keepalives_count", 5)
    DATABASES = {"default": database_config}
else:
    DATABASES = {
        "default": {
            "ENGINE": 'django.db.backends.sqlite3',
            "NAME": BASE_DIR / 'db.sqlite3',
        }
    }

if WHITE_NOISE_INSTALLED:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
