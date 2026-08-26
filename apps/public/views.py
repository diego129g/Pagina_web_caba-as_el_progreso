import datetime
import calendar
import logging

from django.views.generic import TemplateView, DetailView
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from apps.reservas.models import Cabana, Plan, Temporada, Extra, Tarifa, Reserva, Cliente
from .models import Comentario
from .forms import ComentarioForm

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'public/home.html'


class CabanasView(TemplateView):
    template_name = 'public/cabanas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cabanas'] = Cabana.objects.filter(activa=True).prefetch_related('fotos')
        return context


class CabanaDetallesView(DetailView):
    model = Cabana
    template_name = 'public/cabana_detalles.html'
    context_object_name = 'cabana'
    queryset = Cabana.objects.prefetch_related('fotos').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cabanas'] = Cabana.objects.filter(activa=True)
        context['tarifas'] = Tarifa.objects.select_related('plan', 'temporada').all().order_by('temporada__nombre', 'plan__nombre')
        context['extras'] = Extra.objects.filter(activo=True)
        return context


class ServiciosView(TemplateView):
    template_name = 'public/servicios.html'


class GaleriaView(TemplateView):
    template_name = 'public/galeria.html'


class ExperienciasView(TemplateView):
    template_name = 'public/experiencias.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comentarios'] = (
            Comentario.objects
            .filter(activo=True, comentario_padre__isnull=True)
            .prefetch_related('respuestas')
            .select_related('cliente')
        )
        context['form'] = ComentarioForm()
        return context


class NosotrosView(TemplateView):
    template_name = 'public/nosotros.html'


class ContactoView(TemplateView):
    template_name = 'public/contacto.html'


class NuevaReservaView(View):

    def get(self, request):
        context = {
        'cabanas': Cabana.objects.filter(activa=True),
        'tarifas': Tarifa.objects.select_related('plan', 'temporada').all(),
        'extras':  Extra.objects.filter(activo=True),
    }
        return render(request, 'public/reserva_form.html', context)

    def post(self, request):
        from apps.notificaciones.whatsapp import generar_url_whatsapp_formulario
    
        try:
            url_wpp = generar_url_whatsapp_formulario(request.POST)
            return redirect(url_wpp)

        except Exception:
            logger.exception("Error generando el enlace de WhatsApp del formulario de reserva")
            context = {
                'cabanas': Cabana.objects.filter(activa=True),
                'tarifas': Tarifa.objects.select_related('plan', 'temporada').all(),
                'extras':  Extra.objects.filter(activo=True),
                'error': 'No se pudo procesar la solicitud. Revisa los datos ingresados e intenta de nuevo.',
            }
            return render(request, 'public/reserva_form.html', context)

class DisponibilidadView(View):

    def get(self, request):
        cabana_id = request.GET.get('cabana_id')

        if not cabana_id:
            return JsonResponse({'error': 'cabana_id requerido'}, status=400)

        cabana = get_object_or_404(Cabana, pk=cabana_id)

        reservas = list(Reserva.objects.filter(
            cabana_id=cabana_id,
            estado__in=['pendiente', 'confirmada']
        ).values('fecha_inicio', 'fecha_fin'))

        fechas_ocupadas = [
            {'inicio': r['fecha_inicio'].isoformat(), 'fin': r['fecha_fin'].isoformat()}
            for r in reservas
        ]

        data = {
            'cabana_id':   cabana.id,
            'cabana_nombre': cabana.nombre,
            'fechas_ocupadas': fechas_ocupadas,
        }

        month = request.GET.get('month')
        year  = request.GET.get('year')
        if month and year:
            try:
                month = int(month)
                year  = int(year)
                dias_en_mes = set()
                for r in reservas:
                    inicio = r['fecha_inicio']
                    fin    = r['fecha_fin']
                    cur = max(inicio, datetime.date(year, month, 1))
                    ultimo = datetime.date(year, month, calendar.monthrange(year, month)[1])
                    while cur <= fin and cur <= ultimo:
                        dias_en_mes.add(cur.isoformat())
                        cur += datetime.timedelta(days=1)
                data['dias_ocupados'] = sorted(dias_en_mes)
            except (ValueError, TypeError):
                data['dias_ocupados'] = []

        return JsonResponse(data)


# ── Comentarios AJAX ─────────────────────────────────────────────


def _serializar_comentario(comentario):
    return {
        'id': comentario.id,
        'nombre': comentario.nombre,
        'correo': comentario.correo,
        'texto': comentario.texto,
        'creado_at': comentario.creado_at.strftime('%d/%m/%Y %H:%M'),
        'es_respuesta': comentario.es_respuesta(),
        'puede_eliminar': comentario.puede_eliminar(comentario._usuario_solicitante) if hasattr(comentario, '_usuario_solicitante') else False,
    }


@require_POST
def crear_comentario(request):
    form = ComentarioForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errores': form.errors}, status=400)

    comentario = form.save(commit=False)

    cliente = Cliente.objects.filter(correo=comentario.correo).first()
    if cliente:
        comentario.cliente = cliente

    comentario.save()
    comentario._usuario_solicitante = request.user
    return JsonResponse({'ok': True, 'comentario': _serializar_comentario(comentario)})


@require_POST
def responder_comentario(request, pk):
    try:
        padre = Comentario.objects.get(pk=pk, activo=True, comentario_padre__isnull=True)
    except Comentario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Comentario no encontrado.'}, status=404)

    texto = request.POST.get('texto', '').strip()
    if not texto:
        return JsonResponse({'ok': False, 'errores': {'texto': ['Este campo es requerido.']}}, status=400)

    nombre = request.POST.get('nombre', '').strip()
    correo = request.POST.get('correo', '').strip()

    if not nombre or not correo:
        return JsonResponse({'ok': False, 'errores': {'nombre': ['Este campo es requerido.'], 'correo': ['Este campo es requerido.']}}, status=400)

    comentario = Comentario.objects.create(
        nombre=nombre,
        correo=correo,
        texto=texto,
        comentario_padre=padre,
    )

    cliente = Cliente.objects.filter(correo=correo).first()
    if cliente:
        comentario.cliente = cliente
        comentario.save()

    comentario._usuario_solicitante = request.user
    return JsonResponse({'ok': True, 'comentario': _serializar_comentario(comentario)})


@require_POST
def eliminar_comentario(request, pk):
    try:
        comentario = Comentario.objects.get(pk=pk)
    except Comentario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Comentario no encontrado.'}, status=404)

    if not comentario.puede_eliminar(request.user):
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para eliminar este comentario.'}, status=403)

    comentario.activo = False
    comentario.save(update_fields=['activo'])
    return JsonResponse({'ok': True})
