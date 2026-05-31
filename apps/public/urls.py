from django.urls import path
from . import views

urlpatterns = [
    path('',              views.HomeView.as_view(),          name='home'),
    path('cabanas/',      views.CabanasView.as_view(),           name='cabanas'),
    path('cabanas/<int:pk>/', views.CabanaDetallesView.as_view(), name='cabana_detalles'),
    path('cabanas/<int:pk>/', views.CabanaDetallesView.as_view(), name='cabana_detail'),
    path('servicios/',    views.ServiciosView.as_view(),     name='servicios'),
    path('galeria/',      views.GaleriaView.as_view(),       name='galeria'),
    path('experiencias/', views.ExperienciasView.as_view(),  name='experiencias'),
    path('nosotros/',     views.NosotrosView.as_view(),      name='nosotros'),
    path('contacto/',     views.ContactoView.as_view(),      name='contacto'),
    path('reservas/nueva/',          views.NuevaReservaView.as_view(),   name='nueva_reserva'),
    path('reservas/disponibilidad/', views.DisponibilidadView.as_view(), name='disponibilidad'),
]