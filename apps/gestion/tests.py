import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.reservas.models import Cabana, Cliente, Extra, Plan, Reserva, ReservaExtra, Tarifa, Temporada


class EliminarReservaViewTests(TestCase):

    def setUp(self):
        plan = Plan.objects.create(nombre='Plan', duracion_horas=24)
        temporada = Temporada.objects.create(nombre='Temporada')
        tarifa = Tarifa.objects.create(plan=plan, temporada=temporada, precio=Decimal('100000'))
        self.cliente = Cliente.objects.create(nombre='Cliente', documento='1001', telefono='3000000000')
        self.reserva = Reserva.objects.create(
            cliente=self.cliente, cabana=Cabana.objects.create(nombre='Cabaña'), tarifa=tarifa,
            fecha_inicio=datetime.date(2030, 1, 1), fecha_fin=datetime.date(2030, 1, 3),
        )
        extra = Extra.objects.create(nombre='Leña', precio=Decimal('10000'))
        ReservaExtra.objects.create(reserva=self.reserva, extra=extra)
        self.url = reverse('eliminar_reserva', args=[self.reserva.pk])
        self.staff = get_user_model().objects.create_user('admin', password='x', is_staff=True)

    def test_elimina_reserva_y_conserva_cliente(self):
        self.client.force_login(self.staff)
        resp = self.client.post(self.url, {'filtros': 'estado=confirmada&page=3'})
        self.assertRedirects(resp, reverse('reservas_list') + '?estado=confirmada', fetch_redirect_response=False)
        self.assertFalse(Reserva.objects.exists())
        self.assertFalse(ReservaExtra.objects.exists())
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

    def test_no_permite_eliminar_sin_ser_staff(self):
        usuario = get_user_model().objects.create_user('normal', password='x')
        self.client.force_login(usuario)
        self.client.post(self.url)
        self.assertTrue(Reserva.objects.exists())

    def test_get_no_elimina(self):
        self.client.force_login(self.staff)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(Reserva.objects.exists())

    def test_listado_muestra_boton_eliminar(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('reservas_list'))
        self.assertContains(resp, self.url)
        self.assertContains(resp, 'dialogo-eliminar')
