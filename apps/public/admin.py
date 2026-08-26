from django.contrib import admin
from .models import Comentario


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'correo', 'texto_corto', 'comentario_padre', 'activo', 'creado_at']
    list_filter = ['activo', 'creado_at']
    search_fields = ['nombre', 'correo', 'texto']
    readonly_fields = ['cliente', 'creado_at']
    list_editable = ['activo']
    actions = ['aprobar_comentarios', 'ocultar_comentarios']

    def texto_corto(self, obj):
        if len(obj.texto) > 80:
            return obj.texto[:80] + '...'
        return obj.texto
    texto_corto.short_description = 'Comentario'

    @admin.action(description='Aprobar comentarios seleccionados')
    def aprobar_comentarios(self, request, queryset):
        count = queryset.update(activo=True)
        self.message_user(request, f'{count} comentario(s) aprobado(s).')

    @admin.action(description='Ocultar comentarios seleccionados')
    def ocultar_comentarios(self, request, queryset):
        count = queryset.update(activo=False)
        self.message_user(request, f'{count} comentario(s) ocultado(s).')
