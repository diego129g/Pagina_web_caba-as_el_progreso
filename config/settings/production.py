from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     env('DB_NAME'),
        'USER':     env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST':     env('DB_HOST'),
        'PORT':     env('DB_PORT', default='5432'),
    }
}

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True