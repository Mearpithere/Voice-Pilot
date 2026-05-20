from .base import *

DEBUG = True

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Emails go to console in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
