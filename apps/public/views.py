import datetime
import calendar

from django.views.generic import TemplateView, DetailView
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from urllib3 import request
from apps.reservas.models import Cabana, Plan, Temporada, Extra, Tarifa, Reserva


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
    
        except Exception as e:
            context = {
                'cabanas': Cabana.objects.filter(activa=True),
                'tarifas': Tarifa.objects.select_related('plan', 'temporada').all(),
                'extras':  Extra.objects.filter(activo=True),
                'error': str(e),
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
