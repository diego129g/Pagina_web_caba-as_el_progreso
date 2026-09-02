
from django.db import IntegrityError
from apps.reservas.models import Plan, Extra, Temporada,Cabana
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Reserva, ReservaExtra, Cliente, Cabana, Tarifa, Extra


class ReservaExtraSerializer(serializers.ModelSerializer):
    extra_nombre = serializers.CharField(source='extra.nombre', read_only=True)
    precio_unitario = serializers.DecimalField(
        source='extra.precio', max_digits=12, decimal_places=2, read_only=True
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ReservaExtra
        fields = ['id', 'extra', 'extra_nombre', 'cantidad', 'precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()


class ReservaSerializer(serializers.ModelSerializer):
    # Relación M2M con tabla intermedia — se maneja aparte, no como fields = '__all__'
    extras = ReservaExtraSerializer(source='reservaextra_set', many=True, required=False)

    # Campos de solo lectura, útiles para mostrar en la lista sin otra petición
    cliente_nombre = serializers.CharField(source='cliente.__str__', read_only=True)
    cabana_nombre = serializers.CharField(source='cabana.__str__', read_only=True)

    # Campos calculados (métodos del modelo, no columnas de BD)
    total_plan = serializers.SerializerMethodField()
    total_extras = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    valor_restante = serializers.SerializerMethodField()
    nombre_plan_display = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            'id', 'cliente', 'cliente_nombre', 'cabana', 'cabana_nombre',
            'tarifa', 'extras', 'fecha_inicio', 'fecha_fin', 'estado',
            'nombre_plan', 'precio_plan', 'total', 'valor_reserva', 'notas',
            'creado_at',
            'total_plan', 'total_extras', 'subtotal', 'valor_restante',
            'nombre_plan_display',
        ]
        read_only_fields = ['creado_at']

    def get_total_plan(self, obj):
        return obj.total_plan()

    def get_total_extras(self, obj):
        return obj.total_extras()

    def get_subtotal(self, obj):
        return obj.subtotal()

    def get_valor_restante(self, obj):
        return obj.valor_restante()

    def get_nombre_plan_display(self, obj):
        return obj.nombre_plan_display()

    def validate(self, data):
        """Ejecuta el clean() del modelo (fechas, solapamiento) antes de guardar."""
        instance = self.instance if self.instance else Reserva()
        campos_relevantes = ['cliente', 'cabana', 'tarifa', 'fecha_inicio', 'fecha_fin', 'estado']
        for campo in campos_relevantes:
            if campo in data:
                setattr(instance, campo, data[campo])

        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, 'message_dict') else e.messages
            )
        return data

    def create(self, validated_data):
        extras_data = validated_data.pop('reservaextra_set', [])
        reserva = Reserva.objects.create(**validated_data)
        try:
            for extra_data in extras_data:
                ReservaExtra.objects.create(reserva=reserva, **extra_data)
        except IntegrityError:
            raise serializers.ValidationError(
                'No puedes agregar el mismo extra dos veces en la misma reserva.'
            )
        return reserva

    def update(self, instance, validated_data):
        extras_data = validated_data.pop('reservaextra_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if extras_data is not None:
            instance.reservaextra_set.all().delete()
            for extra_data in extras_data:
                ReservaExtra.objects.create(reserva=instance, **extra_data)
        return instance

# serializers.py (continuación del archivo anterior)

class TemporadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Temporada
        fields = ['id', 'nombre']


class PlanSerializer(serializers.ModelSerializer):
    es_dia_de_sol = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ['id', 'nombre', 'descripcion', 'duracion_horas', 'activo', 'es_dia_de_sol']

    def get_es_dia_de_sol(self, obj):
        return obj.es_dia_de_sol()


class TarifaSerializer(serializers.ModelSerializer):
    plan_nombre = serializers.CharField(source='plan.nombre', read_only=True)
    temporada_nombre = serializers.CharField(source='temporada.nombre', read_only=True)

    class Meta:
        model = Tarifa
        fields = ['id', 'plan', 'plan_nombre', 'temporada', 'temporada_nombre', 'precio']

    def validate(self, data):
        # Respeta el unique_together del modelo con un mensaje claro,
        # en vez de dejar que llegue como IntegrityError genérico (500)
        plan = data.get('plan', getattr(self.instance, 'plan', None))
        temporada = data.get('temporada', getattr(self.instance, 'temporada', None))

        query = Tarifa.objects.filter(plan=plan, temporada=temporada)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError(
                'Ya existe una tarifa para este plan en esta temporada.'
            )
        return data


class ExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extra
        fields = ['id', 'nombre', 'descripcion', 'precio', 'activo']

class CabanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cabana
        fields = ['nombre', 'activa', 'descripcion']