from rest_framework import serializers
from django.utils.timezone import now
from .models import Servicio, SolicitudServicio
from usuarios.serializers import UsuarioSerializer
from adopcion.models import Mascota
from adopcion.serializers import MascotaListSerializer


class ServicioSerializer(serializers.ModelSerializer):
    especialista = UsuarioSerializer(read_only=True)
    
    class Meta:
        model = Servicio
        fields = ['idServicio', 'nombre_servicio', 'descripcion', 
                  'precio_base', 'comision', 'especialista']
        read_only_fields = ['idServicio']


class SolicitudServicioSerializer(serializers.ModelSerializer):
    servicio = ServicioSerializer(read_only=True)
    mascota = MascotaListSerializer(read_only=True)
    usuario = UsuarioSerializer(read_only=True)
    servicio_id = serializers.PrimaryKeyRelatedField(queryset=Servicio.objects.all(), write_only=True, source='servicio')
    mascota_id = serializers.PrimaryKeyRelatedField(queryset=Mascota.objects.all(), write_only=True, source='mascota')

    class Meta:
        model = SolicitudServicio
        fields = [
            'idSolicitud', 'servicio', 'servicio_id', 'mascota', 'mascota_id',
            'usuario', 'fecha_solicitud', 'fecha_programada', 'estado',
            'descripcion_problema', 'observaciones_especialista',
            'precio_final', 'fecha_completado'
        ]
        read_only_fields = ['idSolicitud', 'usuario', 'fecha_solicitud', 'estado', 'precio_final', 'fecha_completado']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['usuario'] = request.user
        validated_data['estado'] = 'Pendiente'
        validated_data['fecha_solicitud'] = now()
        return super().create(validated_data)
