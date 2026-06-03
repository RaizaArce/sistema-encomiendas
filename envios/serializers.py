from rest_framework import serializers
from .models import Encomienda, HistorialEstado, Empleado
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoEnvio
from django.utils import timezone


class ClienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()
    esta_activo     = serializers.ReadOnlyField()

    class Meta:
        model  = Cliente
        fields = [
            'id', 'tipo_doc', 'nro_doc',
            'nombres', 'apellidos', 'nombre_completo',
            'telefono', 'email', 'esta_activo',
        ]


class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Ruta
        fields = ['id', 'codigo', 'origen', 'destino', 'precio_base', 'dias_entrega', 'estado']


class HistorialEstadoSerializer(serializers.ModelSerializer):
    empleado_nombre        = serializers.ReadOnlyField(source='empleado.__str__')
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display    = serializers.CharField(source='get_estado_nuevo_display', read_only=True)

    class Meta:
        model  = HistorialEstado
        fields = [
            'id', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display',
            'empleado_nombre', 'observacion', 'fecha_cambio',
        ]


class EncomiendaSerializer(serializers.ModelSerializer):
    remitente_id    = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(), write_only=True, source='ruta'
    )

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente_id', 'destinatario_id', 'ruta_id',
            'estado', 'costo_envio', 'fecha_registro',
            'fecha_entrega_est', 'fecha_entrega_real', 'observaciones',
        ]
        read_only_fields = ['codigo', 'fecha_registro']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['estado_display'] = instance.get_estado_display()
        return data

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else data
        if 'codigo' not in data or not data['codigo']:
            from django.utils import timezone
            import uuid
            data['codigo'] = f'ENC-{timezone.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:6].upper()}'
        return super().to_internal_value(data)

    # Validaciones de campo
    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0 kg.')
        if value > 500:
            raise serializers.ValidationError('El peso maximo permitido es 500 kg.')
        return value

    def validate_codigo(self, value):
        if not value.startswith('ENC-'):
            raise serializers.ValidationError('El codigo debe comenzar con ENC-')
        return value.upper()

    def validate_costo_envio(self, value):
        if value < 0:
            raise serializers.ValidationError('El costo no puede ser negativo.')
        return value

    # Validacion cruzada
    def validate(self, data):
        errors = {}

        if data.get('remitente') and data.get('destinatario') and data['remitente'] == data['destinatario']:
            errors['destinatario'] = 'El destinatario no puede ser el mismo que el remitente.'

        fecha_est = data.get('fecha_entrega_est')
        if fecha_est and fecha_est < timezone.now().date():
            errors['fecha_entrega_est'] = 'La fecha estimada no puede ser en el pasado.'

        ruta  = data.get('ruta')
        costo = data.get('costo_envio')
        if ruta and costo and costo < float(ruta.precio_base):
            errors['costo_envio'] = f'El costo minimo para esta ruta es S/ {ruta.precio_base}.'

        if errors:
            raise serializers.ValidationError(errors)
        return data


class EncomiendaDetailSerializer(serializers.ModelSerializer):
    remitente    = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta         = RutaSerializer(read_only=True)

    remitente_id    = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(), write_only=True, source='ruta'
    )

    historial        = serializers.SerializerMethodField()
    esta_entregada   = serializers.ReadOnlyField()
    tiene_retraso    = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg',
            'remitente', 'remitente_id',
            'destinatario', 'destinatario_id',
            'ruta', 'ruta_id',
            'estado', 'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
            'historial', 'observaciones',
        ]

    def get_historial(self, obj):
        return HistorialEstadoSerializer(obj.historial.all()[:5], many=True).data


class EncomiendaListSerializer(serializers.ModelSerializer):
    remitente_nombre  = serializers.ReadOnlyField(source='remitente.nombre_completo')
    destinatario_nombre = serializers.ReadOnlyField(source='destinatario.nombre_completo')
    estado_display    = serializers.ReadOnlyField(source='get_estado_display')
    ruta_origen       = serializers.ReadOnlyField(source='ruta.origen')
    ruta_destino      = serializers.ReadOnlyField(source='ruta.destino')
    tiene_retraso     = serializers.ReadOnlyField()
    dias_en_transito  = serializers.ReadOnlyField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg',
            'remitente_nombre', 'destinatario_nombre',
            'estado', 'estado_display',
            'ruta_origen', 'ruta_destino',
            'costo_envio', 'fecha_registro',
            'fecha_entrega_est', 'tiene_retraso', 'dias_en_transito',
        ]


class EncomiendaBulkSerializer(serializers.Serializer):
    encomiendas = EncomiendaSerializer(many=True)

    def create(self, validated_data):
        encomiendas_data = validated_data.get('encomiendas', [])
        request = self.context.get('request')
        empleado = request.user.empleado if request and hasattr(request.user, 'empleado') else None

        instances = []
        errors = []
        for i, data in enumerate(encomiendas_data):
            s = EncomiendaSerializer(data=data, context=self.context)
            if s.is_valid():
                instance = s.save(empleado_registro=empleado)
                instances.append(instance)
            else:
                errors.append({'index': i, 'errors': s.errors})

        return {'created': instances, 'errors': errors}


class EncomiendaV2Serializer(serializers.ModelSerializer):
    remitente    = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta         = RutaSerializer(read_only=True)

    remitente_id    = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(), write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(), write_only=True, source='ruta'
    )

    dias_en_transito  = serializers.ReadOnlyField()
    tiene_retraso     = serializers.ReadOnlyField()
    esta_entregada    = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()
    meta              = serializers.SerializerMethodField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta', 'peso_kg', 'costo_envio',
            'remitente', 'remitente_id', 'destinatario', 'destinatario_id', 'ruta', 'ruta_id',
            'estado', 'fecha_registro', 'dias_en_transito', 'tiene_retraso', 'esta_entregada',
            'observaciones', 'meta',
        ]

    def get_meta(self, obj):
        from django.utils import timezone
        return {
            'version':     'v2',
            'generado':    timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'puede_editar': not obj.esta_entregada,
        }
