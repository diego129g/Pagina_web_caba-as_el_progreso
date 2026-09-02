from rest_framework import generics
from apps.reservas.models import Reserva,Plan,Cabana,Extra,Temporada,Tarifa
from apps.reservas.serializers import ReservaSerializer,PlanSerializer,CabanaSerializer,ExtraSerializer,TemporadaSerializer,TarifaSerializer
from rest_framework.exceptions import ValidationError
from django.db.models import ProtectedError

class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError(
                'No se puede eliminar: este plan tiene tarifas asociadas.'
            )
class ReservaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Reserva.objects.select_related('cliente', 'cabana', 'tarifa').all()
    serializer_class = ReservaSerializer
    filterset_fields = ['estado', 'cabana', 'cliente', 'fecha_inicio']

class ReservaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reserva.objects.select_related('cliente', 'cabana', 'tarifa').all()
    serializer_class = ReservaSerializer

class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer



class CabanaListCreateView(generics.ListCreateAPIView):
    queryset = Cabana.objects.all()
    serializer_class = CabanaSerializer

class CabanaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cabana.objects.all()
    serializer_class = CabanaSerializer

class ExtraListCreateView(generics.ListCreateAPIView):
    queryset = Extra.objects.all()
    serializer_class = ExtraSerializer

class ExtraDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Extra.objects.all()
    serializer_class = ExtraSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError(
                'No se puede eliminar: este extra está asociado a reservas.'
            )

class TemporadaListCreateView(generics.ListCreateAPIView):
    queryset = Temporada.objects.all()
    serializer_class = TemporadaSerializer

class TemporadaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Temporada.objects.all()
    serializer_class = TemporadaSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError(
                'No se puede eliminar: esta temporada tiene tarifas asociadas.'
            )

class TarifaListCreateView(generics.ListCreateAPIView):
    queryset = Tarifa.objects.select_related('plan', 'temporada').all()
    serializer_class = TarifaSerializer

class TarifaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tarifa.objects.select_related('plan', 'temporada').all()
    serializer_class = TarifaSerializer