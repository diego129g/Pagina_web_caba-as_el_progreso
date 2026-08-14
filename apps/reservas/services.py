import logging
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_date

from .models import Cabana, Cliente, Reserva, ReservaExtra, Tarifa
from apps.notificaciones.whatsapp import enviar_whatsapp, generar_mensaje_reserva

logger = logging.getLogger(__name__)


class ReservaService:

    def _parsear_fecha(self, valor):
        """Convierte string YYYY-MM-DD a date"""
        if not valor:
            return None
        return parse_date(valor)

    def _parsear_decimal(self, valor):
        """Convierte un valor de formulario a Decimal, o None si viene vacío."""
        if valor in (None, ''):
            return None
        try:
            return Decimal(str(valor))
        except InvalidOperation:
            raise ValidationError(f"'{valor}' no es un valor numérico válido.")

    def crear_reserva(self, data):
        with transaction.atomic():
            # Bloquea la fila de la cabaña para serializar la verificación de
            # solapamiento de fechas: evita que dos reservas creadas casi al
            # mismo tiempo pasen ambas la validación antes de que cualquiera
            # se guarde (doble reserva de la misma cabaña).
            cabana = Cabana.objects.select_for_update().get(pk=data.get('cabana_id'))

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
            nombre_plan = data.get('nombre_plan') if data.get('plan_personalizado') else ''
            reserva = Reserva(
                cliente       = cliente,
                cabana        = cabana,
                tarifa        = tarifa,
                fecha_inicio  = self._parsear_fecha(data.get('fecha_inicio')),
                fecha_fin     = self._parsear_fecha(data.get('fecha_fin')),
                nombre_plan   = nombre_plan or None,
                precio_plan   = self._parsear_decimal(data.get('precio_plan')),
                total         = self._parsear_decimal(data.get('total')),
                valor_reserva = self._parsear_decimal(data.get('valor_reserva')),
                notas         = data.get('notas') or '',
            )

            # 4. Validar (incluye el chequeo de solapamiento, ya protegido por el lock de arriba)
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

        # 7. Notificar por WhatsApp — fuera de la transacción: es I/O externo
        #    y no debe mantener el lock de la cabaña abierto más de lo necesario.
        try:
            telefono = reserva.cliente.telefono
            mensaje  = generar_mensaje_reserva(reserva)
            enviar_whatsapp(telefono, mensaje)
        except Exception:
            logger.exception("Error notificando por WhatsApp la reserva #%s", reserva.id)

        return reserva

    def editar_reserva(self, reserva, data):
        with transaction.atomic():
            cabana = Cabana.objects.select_for_update().get(pk=data.get('cabana_id'))

            estado_anterior = reserva.estado
            estado_nuevo    = data.get('estado', reserva.estado)
            nombre_plan     = data.get('nombre_plan') if data.get('plan_personalizado') else ''

            reserva.cabana        = cabana
            reserva.tarifa_id     = data.get('tarifa_id')
            reserva.fecha_inicio  = self._parsear_fecha(data.get('fecha_inicio'))
            reserva.fecha_fin     = self._parsear_fecha(data.get('fecha_fin'))
            reserva.estado        = estado_nuevo
            reserva.nombre_plan   = nombre_plan or None
            reserva.precio_plan   = self._parsear_decimal(data.get('precio_plan'))
            reserva.total         = self._parsear_decimal(data.get('total'))
            reserva.valor_reserva = self._parsear_decimal(data.get('valor_reserva'))
            reserva.notas         = data.get('notas') or ''

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

        # Notificar por WhatsApp después de actualizar extras (fuera de la transacción)
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
            logger.exception("Error notificando por WhatsApp la reserva #%s", reserva.id)

        return reserva
