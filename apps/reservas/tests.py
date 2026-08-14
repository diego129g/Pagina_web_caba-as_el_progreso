import datetime
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Cabana, Cliente, Extra, Plan, Reserva, ReservaExtra, Tarifa, Temporada
from .services import ReservaService


def _fecha(dias_desde_hoy):
    return datetime.date.today() + datetime.timedelta(days=dias_desde_hoy)


class ReservaOverlapTests(TestCase):
    """Cubre la validación de solapamiento de fechas: es la lógica que
    protege contra la doble reserva de una misma cabaña."""

    def setUp(self):
        self.cabana = Cabana.objects.create(nombre='Cabaña Test')
        self.plan = Plan.objects.create(nombre='Plan Test', duracion_horas=24)
        self.temporada = Temporada.objects.create(nombre='Temporada Test')
        self.tarifa = Tarifa.objects.create(plan=self.plan, temporada=self.temporada, precio=Decimal('200000'))
        self.cliente = Cliente.objects.create(
            nombre='Cliente Uno', documento='1001', telefono='3000000000',
            fecha_nacimiento=datetime.date(1990, 1, 1),
        )

    def _crear_reserva(self, cliente, inicio, fin, estado='confirmada'):
        reserva = Reserva(
            cliente=cliente, cabana=self.cabana, tarifa=self.tarifa,
            fecha_inicio=inicio, fecha_fin=fin, estado=estado,
        )
        reserva.full_clean()
        reserva.save()
        return reserva

    def test_fecha_fin_debe_ser_posterior_a_inicio(self):
        reserva = Reserva(
            cliente=self.cliente, cabana=self.cabana, tarifa=self.tarifa,
            fecha_inicio=_fecha(5), fecha_fin=_fecha(5),
        )
        with self.assertRaises(ValidationError):
            reserva.full_clean()

    def test_permite_reservas_sin_solapamiento(self):
        self._crear_reserva(self.cliente, _fecha(1), _fecha(3))
        # No debería lanzar: rango completamente distinto
        self._crear_reserva(self.cliente, _fecha(10), _fecha(12))
        self.assertEqual(Reserva.objects.count(), 2)

    def test_rechaza_reservas_solapadas_en_la_misma_cabana(self):
        self._crear_reserva(self.cliente, _fecha(1), _fecha(5))

        solapada = Reserva(
            cliente=self.cliente, cabana=self.cabana, tarifa=self.tarifa,
            fecha_inicio=_fecha(3), fecha_fin=_fecha(7),
        )
        with self.assertRaises(ValidationError):
            solapada.full_clean()

    def test_reserva_cancelada_no_bloquea_las_fechas(self):
        self._crear_reserva(self.cliente, _fecha(1), _fecha(5), estado='cancelada')

        # Mismo rango, pero la anterior está cancelada: no debería bloquear.
        nueva = Reserva(
            cliente=self.cliente, cabana=self.cabana, tarifa=self.tarifa,
            fecha_inicio=_fecha(1), fecha_fin=_fecha(5),
        )
        nueva.full_clean()  # no debe lanzar

    def test_editar_la_misma_reserva_no_choca_consigo_misma(self):
        reserva = self._crear_reserva(self.cliente, _fecha(1), _fecha(5))
        reserva.notas = 'actualizada'
        reserva.full_clean()  # no debe lanzar por "solaparse" con su propio registro


class ReservaCalculosTests(TestCase):

    def setUp(self):
        self.cabana = Cabana.objects.create(nombre='Cabaña Test')
        self.plan = Plan.objects.create(nombre='Plan Test', duracion_horas=24)
        self.temporada = Temporada.objects.create(nombre='Temporada Test')
        self.tarifa = Tarifa.objects.create(plan=self.plan, temporada=self.temporada, precio=Decimal('200000'))
        self.extra = Extra.objects.create(nombre='Desayuno', precio=Decimal('15000'))
        self.cliente = Cliente.objects.create(
            nombre='Cliente Dos', documento='1002', telefono='3000000001',
            fecha_nacimiento=datetime.date(1990, 1, 1),
        )
        self.reserva = Reserva.objects.create(
            cliente=self.cliente, cabana=self.cabana, tarifa=self.tarifa,
            fecha_inicio=_fecha(1), fecha_fin=_fecha(3),
            total=Decimal('250000'), valor_reserva=Decimal('100000'),
        )

    def test_subtotal_suma_plan_y_extras(self):
        ReservaExtra.objects.create(reserva=self.reserva, extra=self.extra, cantidad=2)
        # 200000 (plan) + 15000*2 (extras) = 230000
        self.assertEqual(self.reserva.subtotal(), Decimal('230000'))

    def test_valor_restante_resta_lo_ya_pagado(self):
        self.assertEqual(self.reserva.valor_restante(), Decimal('150000'))

    def test_valor_restante_es_none_sin_total(self):
        self.reserva.total = None
        self.assertIsNone(self.reserva.valor_restante())


class ClienteEdadTests(TestCase):

    def test_edad_para_nacido_29_de_febrero(self):
        cliente = Cliente.objects.create(
            nombre='Nacido Bisiesto', documento='2001', telefono='3000000002',
            fecha_nacimiento=datetime.date(2000, 2, 29),
        )
        # No debe lanzar ValueError incluso en años no bisiestos
        edad = cliente.edad()
        self.assertIsInstance(edad, int)
        self.assertGreaterEqual(edad, 0)


class ReservaServiceTests(TestCase):
    """Cubre el flujo completo usado por el panel de gestión."""

    def setUp(self):
        self.cabana = Cabana.objects.create(nombre='Cabaña Servicio')
        self.plan = Plan.objects.create(nombre='Plan Servicio', duracion_horas=24)
        self.temporada = Temporada.objects.create(nombre='Temporada Servicio')
        self.tarifa = Tarifa.objects.create(plan=self.plan, temporada=self.temporada, precio=Decimal('300000'))

    def _datos(self, **overrides):
        datos = {
            'nombre': 'Cliente Servicio',
            'documento': '3001',
            'telefono': '3000000003',
            'correo': '',
            'fecha_nacimiento': '1995-05-05',
            'cabana_id': str(self.cabana.id),
            'tarifa_id': str(self.tarifa.id),
            'fecha_inicio': _fecha(1).isoformat(),
            'fecha_fin': _fecha(3).isoformat(),
            'total': '',
            'valor_reserva': '',
            'precio_plan': '',
            'plan_personalizado': '',
            'nombre_plan': '',
            'notas': '',
        }
        datos.update(overrides)

        class FakeQueryDict(dict):
            def getlist(self, key, default=None):
                value = self.get(key, default if default is not None else [])
                return value if isinstance(value, list) else [value]

        return FakeQueryDict(datos)

    @patch('apps.reservas.services.enviar_whatsapp')
    def test_crear_reserva_crea_cliente_y_reserva(self, mock_enviar):
        reserva = ReservaService().crear_reserva(self._datos())
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(reserva.cabana, self.cabana)
        mock_enviar.assert_called_once()

    @patch('apps.reservas.services.enviar_whatsapp')
    def test_crear_reserva_no_permite_solapar_fechas(self, mock_enviar):
        service = ReservaService()
        service.crear_reserva(self._datos(documento='3001'))
        with self.assertRaises(ValidationError):
            service.crear_reserva(self._datos(documento='3002'))

    @patch('apps.reservas.services.enviar_whatsapp')
    def test_precio_plan_vacio_se_guarda_como_none(self, mock_enviar):
        reserva = ReservaService().crear_reserva(self._datos(precio_plan=''))
        self.assertIsNone(reserva.precio_plan)

    @patch('apps.reservas.services.enviar_whatsapp')
    def test_total_con_valor_cero_se_guarda_como_decimal(self, mock_enviar):
        reserva = ReservaService().crear_reserva(self._datos(total='0'))
        self.assertEqual(reserva.total, Decimal('0'))
