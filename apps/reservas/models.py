from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(unique=True,blank=True,null=True)
    fecha_nacimiento = models.DateField()
    creado_at = models.DateTimeField(auto_now_add=True)

    def edad(self):
        hoy = timezone.now().date()
        cumple = self.fecha_nacimiento.replace(year=hoy.year)
        return hoy.year - self.fecha_nacimiento.year - (1 if hoy < cumple else 0)

    def __str__(self):
        return f"{self.nombre} ({self.documento})"
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

class Cabana(models.Model):
    nombre = models.CharField(max_length=100)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Cabaña"
        verbose_name_plural = "Cabañas"
        ordering = ['nombre']

class Temporada(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"
        

class Plan(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion_horas = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ['nombre']

class Tarifa(models.Model):
    plan      = models.ForeignKey(Plan, on_delete=models.PROTECT)
    temporada = models.ForeignKey(Temporada, on_delete=models.PROTECT)
    precio    = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.plan} - {self.temporada}: ${self.precio:,.0f}"

    class Meta:
        verbose_name        = 'Tarifa'
        verbose_name_plural = 'Tarifas'
        unique_together     = ('plan', 'temporada')

class Extra(models.Model):
    nombre      = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio      = models.DecimalField(max_digits=12, decimal_places=2)
    activo      = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio:,.0f})"

    class Meta:
        verbose_name        = 'Extra'
        verbose_name_plural = 'Extras'
        ordering            = ['precio']

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    cabana  = models.ForeignKey(Cabana, on_delete=models.PROTECT)
    tarifa  = models.ForeignKey(Tarifa, on_delete=models.PROTECT)
    extra = models.ManyToManyField(Extra, through='ReservaExtra', blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='confirmada')
    nombre_plan = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del plan personalizado")
    precio_plan = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio personalizado del plan")
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Total manual")
    valor_reserva = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Valor con el que reservó")
    notas = models.TextField(blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.fecha_inicio and self.fecha_fin:

            # Fecha fin debe ser posterior a fecha inicio
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError('La fecha de salida debe ser posterior a la de entrada.')

            # Verificar solapamiento en la misma cabaña
            solapadas = Reserva.objects.filter(
                cabana=self.cabana,
                estado__in=['pendiente', 'confirmada'],
                fecha_inicio__lt=self.fecha_fin,
                fecha_fin__gt=self.fecha_inicio,
            )

            # Si es edición excluir la reserva actual
            if self.pk:
                solapadas = solapadas.exclude(pk=self.pk)

            if solapadas.exists():
                raise ValidationError(
                    f"La cabaña '{self.cabana}' ya tiene una reserva en ese rango de fechas."
                )
    
    def total_plan(self):
        if self.precio_plan is not None:
            return self.precio_plan
        return self.tarifa.precio
    
    def total_extras(self):
        return sum(re.extra.precio * re.cantidad for re in self.reservaextra_set.all()
                   )
    
    def subtotal(self):
        return self.total_plan() + self.total_extras()

    def valor_restante(self):
        if self.total is not None:
            return self.total - (self.valor_reserva or 0)
        return None

    def nombre_plan_display(self):
        if self.nombre_plan:
            return self.nombre_plan
        return self.tarifa.plan.nombre

    def __str__(self):
        return f"Reserva #{self.id} — {self.cliente} — {self.cabana}"

    class Meta:
        verbose_name        = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering            = ['-fecha_inicio']
        indexes             = [
            models.Index(fields=['cliente'],                             name='idx_reservas_cliente'),
            models.Index(fields=['cabana', 'fecha_inicio', 'fecha_fin'], name='idx_reservas_rango_fechas'),
            models.Index(fields=['fecha_inicio'],                        name='idx_reservas_fecha_inicio'),
        ]

class ReservaExtra(models.Model):
    reserva  = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    extra    = models.ForeignKey(Extra, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.extra.precio * self.cantidad

    def __str__(self):
        return f"{self.reserva} — {self.extra} x{self.cantidad}"

    class Meta:
        verbose_name        = 'Extra de Reserva'
        verbose_name_plural = 'Extras de Reserva'
        unique_together     = ('reserva', 'extra')