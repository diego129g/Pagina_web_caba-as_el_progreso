from django.conf import settings
from django.shortcuts import render

# Rutas que deben quedar siempre accesibles, incluso en modo mantenimiento:
# /admin/ para poder seguir administrando el sitio, /static/ para que los
# estáticos de la propia página de mantenimiento (y del admin) carguen bien.
EXEMPT_PATH_PREFIXES = ('/admin/', '/static/')


class MaintenanceModeMiddleware:
    """
    Si settings.MAINTENANCE_MODE está activo, corta el flujo antes de llegar
    a la vista y devuelve una página 503 de "sitio en construcción".

    Se puede sortear visitando cualquier URL con ?preview=<MAINTENANCE_BYPASS_KEY>
    una vez: el bypass queda guardado en la sesión y no hay que repetir el
    parámetro en cada página durante esa sesión.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.MAINTENANCE_MODE:
            return self.get_response(request)

        if request.path.startswith(EXEMPT_PATH_PREFIXES):
            return self.get_response(request)

        bypass_key = settings.MAINTENANCE_BYPASS_KEY
        preview_param = request.GET.get('preview')

        if bypass_key and preview_param == bypass_key:
            request.session['maintenance_bypass'] = True

        if request.session.get('maintenance_bypass'):
            return self.get_response(request)

        return render(request, 'maintenance.html', status=503)
