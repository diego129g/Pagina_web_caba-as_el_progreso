from django.urls import path
from apps.reservas.api_views import ReservaListCreateAPIView

urlpatterns = [
    path('reservas/', ReservaListCreateAPIView.as_view()),
]