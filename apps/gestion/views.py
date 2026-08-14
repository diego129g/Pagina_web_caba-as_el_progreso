import logging

from django.views.generic import TemplateView, ListView, DetailView
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from .mixins import AdminRequiredMixin
from apps.reservas.models import Reserva, Cliente, Cabana, Tarifa, Extra

logger = logging.getLogger(__name__)


class AdminLoginView(LoginView):
    template_name    = 'gestion/login.html'
    next_page        = reverse_lazy('dashboard')

    MAX_INTENTOS     = 5
    BLOQUEO_SEGUNDOS = 300  # 5 minutos

    def _cache_key(self):
        ip = self.request.META.get('REMOTE_ADDR', 'unknown')
        return f'gestion_login_intentos_{ip}'

    def post(self, request, *args, **kwargs):
        # Protección básica contra fuerza bruta: bloquea intentos tras varias
        # credenciales inválidas seguidas desde la misma IP.
        if cache.get(self._cache_key(), 0) >= self.MAX_INTENTOS:
            form = self.get_form()
            form.add_error(None, 'Demasiados intentos fallidos. Espera unos minutos antes de volver a intentar.')
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        cache.set(self._cache_key(), cache.get(self._cache_key(), 0) + 1, self.BLOQUEO_SEGUNDOS)
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(self._cache_key())
        return super().form_valid(form)


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy('admin_login')


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'gestion/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pendientes']  = Reserva.objects.filter(estado='pendiente').count()
        context['confirmadas'] = Reserva.objects.filter(estado='confirmada').count()
        context['recientes']   = Reserva.objects.select_related('cliente', 'cabana').order_by('-creado_at')[:5]
        return context


class ReservasListView(AdminRequiredMixin, ListView):
    model               = Reserva
    template_name       = 'gestion/reservas_list.html'
    context_object_name = 'reservas'
    ordering            = ['-fecha_inicio']
    paginate_by         = 25

    def get_queryset(self):
        qs     = super().get_queryset().select_related('cliente', 'cabana', 'tarifa__plan')
        estado = self.request.GET.get('estado')
        cabana = self.request.GET.get('cabana')
        fecha  = self.request.GET.get('fecha')
        if estado:
            qs = qs.filter(estado=estado)
        if cabana:
            qs = qs.filter(cabana_id=cabana)
        if fecha:
            qs = qs.filter(fecha_inicio__date=fecha)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cabanas'] = Cabana.objects.filter(activa=True)
        return context


class ReservaDetailView(AdminRequiredMixin, DetailView):
    model               = Reserva
    template_name       = 'gestion/reserva_detail.html'
    context_object_name = 'reserva'
    queryset            = Reserva.objects.select_related(
        'cliente', 'cabana', 'tarifa__plan', 'tarifa__temporada'
    ).prefetch_related('reservaextra_set__extra')


class NuevaReservaAdminView(AdminRequiredMixin, View):

    def get(self, request):
        context = {
            'cabanas':  Cabana.objects.filter(activa=True),
            'tarifas':  Tarifa.objects.select_related('plan', 'temporada').all(),
            'extras':   Extra.objects.filter(activo=True),
            'clientes': Cliente.objects.all(),
        }
        return render(request, 'gestion/reserva_form.html', context)

    def post(self, request):
        from apps.reservas.services import ReservaService
        try:
            ReservaService().crear_reserva(request.POST)
            return redirect('reservas_list')
        except Exception:
            logger.exception("Error creando reserva desde el panel de gestión")
            context = {
                'cabanas':             Cabana.objects.filter(activa=True),
                'tarifas':             Tarifa.objects.select_related('plan', 'temporada').all(),
                'extras':              Extra.objects.filter(activo=True),
                'clientes':            Cliente.objects.all(),
                'error':               'No se pudo crear la reserva. Revisa los datos ingresados e intenta de nuevo.',
                'form_data':           request.POST,
                'extras_seleccionados': request.POST.getlist('extras'),
            }
            return render(request, 'gestion/reserva_form.html', context)


class ReservaEditView(AdminRequiredMixin, View):

    def get(self, request, pk):
        reserva = get_object_or_404(Reserva, pk=pk)
        context = {
            'reserva':  reserva,
            'cabanas':  Cabana.objects.filter(activa=True),
            'tarifas':  Tarifa.objects.select_related('plan', 'temporada').all(),
            'extras':   Extra.objects.filter(activo=True),
            'clientes': Cliente.objects.all(),
        }
        return render(request, 'gestion/reserva_form.html', context)

    def post(self, request, pk):
        from apps.reservas.services import ReservaService
        reserva = get_object_or_404(Reserva, pk=pk)
        try:
            ReservaService().editar_reserva(reserva, request.POST)
            return redirect('reserva_detail', pk=pk)
        except Exception:
            logger.exception("Error editando reserva #%s desde el panel de gestión", pk)
            context = {
                'reserva':             reserva,
                'cabanas':             Cabana.objects.filter(activa=True),
                'tarifas':             Tarifa.objects.select_related('plan', 'temporada').all(),
                'extras':              Extra.objects.filter(activo=True),
                'clientes':            Cliente.objects.all(),
                'error':               'No se pudo guardar la reserva. Revisa los datos ingresados e intenta de nuevo.',
                'form_data':           request.POST,
                'extras_seleccionados': request.POST.getlist('extras'),
            }
            return render(request, 'gestion/reserva_form.html', context)


class ConfirmarReservaView(AdminRequiredMixin, View):

    def post(self, request, pk):
        reserva        = get_object_or_404(Reserva, pk=pk)
        reserva.estado = 'confirmada'
        reserva.save()
        return redirect('reserva_detail', pk=pk)


class CancelarReservaView(AdminRequiredMixin, View):

    def post(self, request, pk):
        reserva        = get_object_or_404(Reserva, pk=pk)
        reserva.estado = 'cancelada'
        reserva.save()
        return redirect('reserva_detail', pk=pk)


class DisponibilidadGestionView(AdminRequiredMixin, TemplateView):
    template_name = 'gestion/disponibilidad.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cabanas'] = Cabana.objects.filter(activa=True)
        return context


class BuscarClienteView(AdminRequiredMixin, View):

    def get(self, request):
        documento = request.GET.get('documento', '')
        try:
            cliente = Cliente.objects.get(documento=documento)
            return JsonResponse({
                'encontrado': True,
                'cliente': {
                    'nombre':           cliente.nombre,
                    'telefono':         cliente.telefono,
                    'correo':           cliente.correo or '',
                    'fecha_nacimiento': cliente.fecha_nacimiento.isoformat(),
                }
            })
        except Cliente.DoesNotExist:
            return JsonResponse({'encontrado': False})
