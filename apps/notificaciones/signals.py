from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.reservas.models import Reserva
from .whatsapp import enviar_whatsapp, generar_mensaje_reserva, _mensaje_cancelada
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Reserva)
def guardar_estado_anterior(sender, instance, **kwargs):
    """
    Antes de guardar, memoriza el estado anterior
    para detectar cambios en post_save.
    """
    if instance.pk:
        try:
            instance._estado_anterior = Reserva.objects.get(pk=instance.pk).estado
        except Reserva.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Reserva)
def notificar_reserva(sender, instance, created, **kwargs):
    """
    Envía WhatsApp al cliente según el evento:
    - Reserva creada (admin) → aviso de recepción
    - Cambio a confirmada    → aviso de recepción (funcion_generar)
    - Cambio a cancelada     → aviso de cancelación
    """
    try:
        # Si el servicio ya manejó la notificación, no duplicar
        if getattr(instance, '_skip_notificacion', False):
            return

        telefono = instance.cliente.telefono

        if created:
            return

        else:
            estado_anterior = getattr(instance, '_estado_anterior', None)
            estado_actual   = instance.estado

            if estado_anterior == estado_actual:
                # No hubo cambio de estado — no notificar
                return

            if estado_actual == 'confirmada':
                mensaje = generar_mensaje_reserva(instance)
                enviar_whatsapp(telefono, mensaje)

            elif estado_actual == 'cancelada':
                mensaje = _mensaje_cancelada(instance)
                enviar_whatsapp(telefono, mensaje)

    except Exception as e:
        logger.error(f"Error en signal notificar_reserva: {e}")


