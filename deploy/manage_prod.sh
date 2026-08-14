#!/usr/bin/env bash
# Ejecuta manage.py con los settings de producción, sin tener que exportar
# DJANGO_SETTINGS_MODULE a mano cada vez.
#
# Uso:
#   ./deploy/manage_prod.sh migrate --noinput
#   ./deploy/manage_prod.sh collectstatic --noinput
#   ./deploy/manage_prod.sh createsuperuser
set -euo pipefail

cd "$(dirname "$0")/.."
export DJANGO_SETTINGS_MODULE=config.settings.production
./venv/bin/python manage.py "$@"
