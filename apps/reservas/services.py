from django.core.exceptions import ValidationError
from .models import Cliente, Reserva, ReservaExtra, Tarifa
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from apps.notificaciones.whatsapp import enviar_whatsapp, generar_mensaje_reserva

class ReservaService:

    def _parsear_fecha(self, valor):
        """Convierte string datetime-local a datetime con timezone"""
        if not valor:
            return None
        dt = parse_datetime(valor)
        if dt and timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt

    def crear_reserva(self, data):
        # 1. Crear o recuperar cliente
        cliente, _ = Cliente.objects.update_or_create(
            documento=data.get('documento'),
            defaults={
                'nombre':           data.get('nombre'),
                'telefono':         data.get('telefono'),
                'correo':           data.get('correo') or None,
                'fecha_nacimiento': data.get('fecha_nacimiento'),
            }
        )

        # 2. Obtener tarifa
        tarifa = Tarifa.objects.get(pk=data.get('tarifa_id'))

        # 3. Construir reserva
        reserva = Reserva(
            cliente      = cliente,
            cabana_id    = data.get('cabana_id'),
            tarifa       = tarifa,
            fecha_inicio = self._parsear_fecha(data.get('fecha_inicio')),
            fecha_fin    = self._parsear_fecha(data.get('fecha_fin')),
            notas        = data.get('notas') or '',
        )

        # 4. Validar
        reserva.full_clean()

        # 5. Guardar (la notificación se envía manualmente tras crear los extras)
        reserva._skip_notificacion = True
        reserva.save()

        # 6. Asociar extras
        extras_ids = data.getlist('extras') if hasattr(data, 'getlist') else data.get('extras', [])
        for extra_id in extras_ids:
            ReservaExtra.objects.create(
                reserva = reserva,
                extra_id = extra_id,
                cantidad = 1
            )

        # 7. Notificar por WhatsApp (después de crear extras para que aparezcan en el mensaje)
        try:
            telefono = reserva.cliente.telefono
            mensaje  = generar_mensaje_reserva(reserva)
            enviar_whatsapp(telefono, mensaje)
        except Exception:
            pass

        return reserva

    def editar_reserva(self, reserva, data):
        estado_anterior = reserva.estado
        estado_nuevo    = data.get('estado', reserva.estado)

        reserva.cabana_id    = data.get('cabana_id')
        reserva.tarifa_id    = data.get('tarifa_id')
        reserva.fecha_inicio = self._parsear_fecha(data.get('fecha_inicio'))
        reserva.fecha_fin    = self._parsear_fecha(data.get('fecha_fin'))
        reserva.estado       = estado_nuevo
        reserva.notas        = data.get('notas') or ''

        reserva.full_clean()
        reserva._skip_notificacion = True  # la enviamos manualmente después de extras
        reserva.save()

        reserva.reservaextra_set.all().delete()
        extras_ids = data.getlist('extras') if hasattr(data, 'getlist') else data.get('extras', [])
        for extra_id in extras_ids:
            ReservaExtra.objects.create(
                reserva_id = reserva.id,
                extra_id   = extra_id,
                cantidad   = 1
            )

        # Notificar si cambió el estado (después de extras para que aparezcan en el mensaje)
        if estado_anterior != estado_nuevo:
            try:
                telefono = reserva.cliente.telefono
                if estado_nuevo == 'confirmada':
                    mensaje = generar_mensaje_reserva(reserva)
                elif estado_nuevo == 'cancelada':
                    from apps.notificaciones.whatsapp import _mensaje_cancelada
                    mensaje = _mensaje_cancelada(reserva)
                else:
                    mensaje = None
                if mensaje:
                    enviar_whatsapp(telefono, mensaje)
            except Exception:
                pass

        return reserva