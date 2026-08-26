from django.db import models
from django.conf import settings


class Comentario(models.Model):
    cliente = models.ForeignKey(
        'reservas.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comentarios',
        verbose_name='Cliente vinculado',
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    correo = models.EmailField(verbose_name='Correo electrónico')
    texto = models.TextField(max_length=1000, verbose_name='Comentario')
    comentario_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='respuestas',
        verbose_name='Comentario padre',
    )
    activo = models.BooleanField(default=True, verbose_name='Visible')
    creado_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    def es_respuesta(self):
        return self.comentario_padre_id is not None

    def puede_eliminar(self, usuario):
        if not usuario.is_authenticated:
            return False
        if usuario.is_staff:
            return True
        return usuario.email == self.correo

    def __str__(self):
        prefijo = '→ ' if self.es_respuesta() else ''
        return f"{prefijo}{self.nombre}: {self.texto[:50]}"

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['-creado_at']
