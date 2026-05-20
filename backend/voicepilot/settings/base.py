from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('DJANGO_SECRET_KEY', default='change-me-in-production')
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_celery_beat',
    'storages',
    # Local apps
    'apps.clinics',
    'apps.calls',
    'apps.appointments',
    'apps.webhooks',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'voicepilot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'voicepilot.wsgi.application'
ASGI_APPLICATION = 'voicepilot.asgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── REST Framework ────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://localhost:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ── Plivo ─────────────────────────────────────────────────────────────────────
PLIVO_AUTH_ID = config('PLIVO_AUTH_ID', default='')
PLIVO_AUTH_TOKEN = config('PLIVO_AUTH_TOKEN', default='')
PLIVO_WEBHOOK_BASE_URL = config('PLIVO_WEBHOOK_BASE_URL', default='http://localhost:8000')

# ── LiveKit ───────────────────────────────────────────────────────────────────
LIVEKIT_URL = config('LIVEKIT_URL', default='wss://your-project.livekit.cloud')
LIVEKIT_API_KEY = config('LIVEKIT_API_KEY', default='')
LIVEKIT_API_SECRET = config('LIVEKIT_API_SECRET', default='')

# ── Deepgram ──────────────────────────────────────────────────────────────────
DEEPGRAM_API_KEY = config('DEEPGRAM_API_KEY', default='')

# ── Google AI (Gemini) ────────────────────────────────────────────────────────
GOOGLE_AI_API_KEY = config('GOOGLE_AI_API_KEY', default='')

# ── Cartesia ──────────────────────────────────────────────────────────────────
CARTESIA_API_KEY = config('CARTESIA_API_KEY', default='')
CARTESIA_VOICE_ID = config('CARTESIA_VOICE_ID', default='a0e99841-438c-4a64-b679-ae501e7d6091')

# ── Google Calendar ───────────────────────────────────────────────────────────
GOOGLE_CALENDAR_CREDENTIALS_JSON = config('GOOGLE_CALENDAR_CREDENTIALS_JSON', default='')

# ── Airtable ──────────────────────────────────────────────────────────────────
AIRTABLE_API_KEY = config('AIRTABLE_API_KEY', default='')
AIRTABLE_BASE_ID = config('AIRTABLE_BASE_ID', default='')

# ── AWS S3 ────────────────────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='voicepilot-recordings')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ap-south-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'private'
