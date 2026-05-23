import urllib.parse
import requests
import logging
from django.conf import settings

from apps.reservas.models import Cabana, Tarifa

logger = logging.getLogger(__name__)




def mensaje_reserva_formulario(data):
    cabana = Cabana.objects.get(pk=data.get("cabana_id"))
    tarifa = Tarifa.objects.select_related("plan", "temporada").get(pk=data.get("tarifa_id"))

    nombre = data.get("nombre")
    documento = data.get("documento")
    telefono = data.get("telefono")
    correo = data.get("correo")
    extras = data.get("extras", [])
    fecha_inicio = data.get("fecha_inicio")
    fecha_fin = data.get("fecha_fin")

    mensaje = f""" *Hola estoy interesad@ en hacer una reserva*

👤 Nombre: {nombre}
👤 Documento: {documento}
📞 Teléfono: {telefono}
📧 Correo: {correo}
🏡 Cabaña: {cabana.nombre}
🎯 Plan: {tarifa.plan.nombre}
🗓️ Temporada: {tarifa.temporada.nombre}
🎁 Extras: {', '.join([f'{e.nombre} x{e.cantidad}' for e in extras])}

📅 Entrada: {fecha_inicio}
📅 Salida: {fecha_fin}
"""

    return mensaje






def generar_mensaje_reserva(reserva):
    """Genera el texto completo del mensaje de confirmación."""

    extras = reserva.reservaextra_set.select_related('extra').all()

    mensaje = f"""✅ *Reserva recibida — Cabañas El Progreso*

Hola *{reserva.cliente.nombre}*, recibimos tu solicitud de reserva. Aquí están los detalles:

🏡 *Cabaña:* {reserva.cabana.nombre}
🎯 *Plan:* {reserva.tarifa.plan.nombre}
🗓️ *Temporada:* {reserva.tarifa.temporada.nombre}
📅 *Entrada:* {reserva.fecha_inicio.strftime('%d/%m/%Y a las %H:%M')}
📅 *Salida:* {reserva.fecha_fin.strftime('%d/%m/%Y a las %H:%M')}
👤 *Cliente:* {reserva.cliente.nombre}
📄 *Documento:* {reserva.cliente.documento}
📞 *Teléfono:* {reserva.cliente.telefono}"""

    if extras:
        mensaje += "\n\n🎁 *Extras solicitados:*"
        for re in extras:
            mensaje += f"\n  • {re.extra.nombre} x{re.cantidad} — ${re.subtotal():,.0f}"

    mensaje += f"""

💰 *Valor del plan:* ${reserva.total_plan():,.0f}"""

    if extras:
        mensaje += f"\n💰 *Valor extras:* ${reserva.total_extras():,.0f}"

    mensaje += f"""
💰 *Total a pagar:* ${reserva.total():,.0f}

🔖 *Número de reserva:* #{reserva.id}



¡Gracias por elegirnos! 🌿"""

    return mensaje




def _mensaje_cancelada(reserva):
    return f"""❌ *Reserva Cancelada — Cabañas El Progreso*

Hola *{reserva.cliente.nombre}*, lamentamos informarte que tu reserva *#{reserva.id}* ha sido cancelada.

Si tienes alguna duda o deseas hacer una nueva reserva, escríbenos con gusto te ayudamos. 🌿"""





def generar_url_whatsapp(reserva):
    """Genera URL de WhatsApp con mensaje prellenado (para redirección del cliente)."""
    numero  = settings.WASENDERAPPI_PHONE  
    mensaje = generar_mensaje_reserva(reserva)
    return f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"


def generar_url_whatsapp_formulario(data):
    """Genera URL de WhatsApp con mensaje prellenado a partir de datos del formulario."""
    mensaje = mensaje_reserva_formulario(data)
    numero  = settings.WASENDERAPPI_PHONE
    return f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"


def enviar_whatsapp(telefono, mensaje):
    """Envía mensaje via API de Wasenderappi."""
    api_key = settings.WASENDERAPPI_API_KEY

    if not api_key:
        logger.warning("WASENDERAPPI_API_KEY no configurada — mensaje no enviado.")
        return False

    # Formatear teléfono — asegurarse que tenga código de país
    telefono = telefono.strip().replace(' ', '').replace('-', '')
    if not telefono.startswith('+'):
        telefono = f"+{telefono}"

    try:
        response = requests.post(
            'https://www.wasenderapi.com/api/send-message',
            headers={
                'Authorization': f'Bearer {'65b00faf5f080308958a7d3e9325799cde71b798fd17efaa9ee56568bbd78082'}',
                'Content-Type':  'application/json',
            },
            json={
                'to':   telefono,
                'text': mensaje,
            },
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"WhatsApp enviado correctamente a {telefono}")
            return True
        else:
            logger.error(f"Error Wasenderappi {response.status_code}: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con Wasenderappi: {e}")
        return False