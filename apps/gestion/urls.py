from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.DashboardView.as_view(),             name='dashboard'),
    path('login/',                        views.AdminLoginView.as_view(),             name='admin_login'),
    path('logout/',                       views.AdminLogoutView.as_view(),            name='admin_logout'),
    path('reservas/',                     views.ReservasListView.as_view(),           name='reservas_list'),
    path('reservas/nueva/',               views.NuevaReservaAdminView.as_view(),      name='reserva_nueva_admin'),
    path('reservas/<int:pk>/',            views.ReservaDetailView.as_view(),          name='reserva_detail'),
    path('reservas/<int:pk>/editar/',     views.ReservaEditView.as_view(),            name='reserva_editar'),
    path('reservas/<int:pk>/confirmar/',  views.ConfirmarReservaView.as_view(),       name='confirmar_reserva'),
    path('reservas/<int:pk>/cancelar/',   views.CancelarReservaView.as_view(),        name='cancelar_reserva'),
    path('disponibilidad/',               views.DisponibilidadGestionView.as_view(),  name='disponibilidad_gestion'),
]