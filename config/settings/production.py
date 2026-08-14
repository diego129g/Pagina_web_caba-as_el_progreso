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

# Mientras el sitio sirva solo por IP (sin dominio ni certificado TLS), esto
# debe quedar en False — si no, Django exige HTTPS para todo (redirects y
# cookies) y la app queda inaccesible. El día que haya dominio + certbot,
# poner DJANGO_USE_HTTPS=True en el .env del servidor y reiniciar gunicorn.
USE_HTTPS = env.bool('DJANGO_USE_HTTPS', default=False)

CSRF_COOKIE_SECURE = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
SECURE_SSL_REDIRECT = USE_HTTPS

if USE_HTTPS:
    # La app corre detrás de un proxy (nginx) que termina TLS y reenvía la
    # petición por HTTP internamente — sin este header Django no puede saber
    # que la conexión original era HTTPS.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 semana; subir gradualmente tras confirmar que todo sirve por HTTPS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True