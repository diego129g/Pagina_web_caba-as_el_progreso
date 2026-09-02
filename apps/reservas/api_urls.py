from django.urls import path
from apps.reservas.api_views import (ReservaListCreateAPIView, TemporadaDetailView,
ReservaDetailView, PlanListCreateView, PlanDetailView, CabanaListCreateView,
CabanaDetailView, ExtraListCreateView, ExtraDetailView, TemporadaListCreateView, TarifaListCreateView, TarifaDetailView)

urlpatterns = [
    path('reservas/', ReservaListCreateAPIView.as_view()),
    path('reservas/<int:pk>/', ReservaDetailView.as_view()),
    path('planes/', PlanListCreateView.as_view()),
    path('planes/<int:pk>/', PlanDetailView.as_view()),
    path('cabanas/', CabanaListCreateView.as_view()),
    path('cabanas/<int:pk>/', CabanaDetailView.as_view()),
    path('extras/', ExtraListCreateView.as_view()),
    path('extras/<int:pk>/', ExtraDetailView.as_view()),
    path('temporadas/', TemporadaListCreateView.as_view()),
    path('temporadas/<int:pk>/', TemporadaDetailView.as_view()),
    path('tarifas/', TarifaListCreateView.as_view()),
    path('tarifas/<int:pk>/', TarifaDetailView.as_view()),
]