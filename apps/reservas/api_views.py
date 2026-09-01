from rest_framework import generics
from apps.reservas.models import Reserva
from apps.reservas.serializers import ReservaSerializer

class ReservaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer