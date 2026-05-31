from django.core.exceptions import ValidationError
from .models import Cliente, Reserva, ReservaExtra, Tarifa
from django.utils.dateparse import parse_date
from apps.notificaciones.whatsapp import enviar_whatsapp, generar_mensaje_reserva

class ReservaService:

    def _parsear_fecha(self, valor):
        """Convierte string YYYY-MM-DD a date"""
        if not valor:
            return None
        return parse_date(valor)

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
        total = data.get('total')
        valor_reserva = data.get('valor_reserva')
        precio_plan = data.get('precio_plan')
        nombre_plan = data.get('nombre_plan') if data.get('plan_personalizado') else ''
        reserva = Reserva(
            cliente      = cliente,
            cabana_id    = data.get('cabana_id'),
            tarifa       = tarifa,
            fecha_inicio = self._parsear_fecha(data.get('fecha_inicio')),
            fecha_fin    = self._parsear_fecha(data.get('fecha_fin')),
            nombre_plan  = nombre_plan or None,
            precio_plan  = precio_plan if precio_plan else None,
            total        = total if total else None,
            valor_reserva = valor_reserva if valor_reserva else None,
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

        total = data.get('total')
        valor_reserva = data.get('valor_reserva')
        precio_plan = data.get('precio_plan')
        nombre_plan = data.get('nombre_plan') if data.get('plan_personalizado') else ''
        reserva.cabana_id    = data.get('cabana_id')
        reserva.tarifa_id    = data.get('tarifa_id')
        reserva.fecha_inicio = self._parsear_fecha(data.get('fecha_inicio'))
        reserva.fecha_fin    = self._parsear_fecha(data.get('fecha_fin'))
        reserva.estado       = estado_nuevo
        reserva.nombre_plan  = nombre_plan or None
        reserva.precio_plan  = precio_plan if precio_plan else None
        reserva.total        = total if total else None
        reserva.valor_reserva = valor_reserva if valor_reserva else None
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

        # Notificar por WhatsApp después de actualizar extras
        try:
            telefono = reserva.cliente.telefono
            if estado_nuevo == 'confirmada':
                mensaje = generar_mensaje_reserva(reserva)
            elif estado_nuevo == 'cancelada' and estado_anterior != estado_nuevo:
                from apps.notificaciones.whatsapp import _mensaje_cancelada
                mensaje = _mensaje_cancelada(reserva)
            else:
                mensaje = None
            if mensaje:
                enviar_whatsapp(telefono, mensaje)
        except Exception:
            pass

        return reserva