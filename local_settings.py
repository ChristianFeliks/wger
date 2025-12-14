# local_settings.py
from wger.settings_global import *
import os

DEBUG = True
SECRET_KEY = 'dev-local-2Lk^z6#x5mFq9!p@XbC1t$Yw3r%V8nZ0q&Hu4*DsKeMjA7P!Q'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
    }
}

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
MEDIA_URL = '/media/'
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Silence reCAPTCHA test-key warning for local/test runs
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']