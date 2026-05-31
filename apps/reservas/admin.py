from django.contrib import admin
from .models import Cliente, Cabana, Temporada, Plan, Tarifa, Extra, Reserva, ReservaExtra


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display   = ['nombre', 'documento', 'telefono', 'correo', 'fecha_nacimiento']
    search_fields  = ['nombre', 'documento', 'telefono']
    ordering       = ['nombre']


@admin.register(Cabana)
class CabanaAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'activa']
    list_filter   = ['activa']
    ordering      = ['nombre']


@admin.register(Temporada)
class TemporadaAdmin(admin.ModelAdmin):
    list_display = ['nombre']


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'duracion_horas', 'activo']
    list_filter   = ['activo']
    ordering      = ['nombre']


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display  = ['plan', 'temporada', 'precio']
    list_filter   = ['plan', 'temporada']
    ordering      = ['plan__nombre']


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'precio', 'activo']
    list_filter   = ['activo']
    ordering      = ['precio']


class ReservaExtraInline(admin.TabularInline):
    model  = ReservaExtra
    extra  = 1


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display   = ['id', 'cliente', 'cabana', 'fecha_inicio', 'fecha_fin', 'estado', 'precio_plan', 'total', 'valor_reserva']
    list_filter    = ['estado', 'cabana', 'fecha_inicio']
    search_fields  = ['cliente__nombre', 'cliente__documento']
    date_hierarchy = 'fecha_inicio'
    ordering       = ['-fecha_inicio']
    inlines        = [ReservaExtraInline]
