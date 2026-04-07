from rest_framework import serializers
from .models import Mascota, Adopcion, Calificacion, Notificacion, ChatMessage
from django.utils.timezone import now
from usuarios.models import Usuario
from usuarios.serializers import UsuarioSerializer


class MascotaListSerializer(serializers.ModelSerializer):
    """Serializador simple para listados de mascotas"""
    class Meta:
        model = Mascota
        fields = ['idMascota', 'Nombre_Mascota', 'Especie', 'Raza', 'Genero', 'Peso', 'Estado_Salud', 'Esterilizado', 'Socializado']

class MascotaDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para mascotas"""
    class Meta:
        model = Mascota
        fields = '__all__'

class AdopcionListSerializer(serializers.ModelSerializer):
    """Serializador para listados de adopciones"""
    mascota_info = MascotaListSerializer(source='idMascota', read_only=True)
    
    class Meta:
        model = Adopcion
        fields = ['idAdopcion', 'idPropietario', 'idMascota', 'mascota_info', 'Estado', 
                  'Fecha_Solicitud', 'Fecha_Adopción', 'Motivo_Adopción', 'Estado_Solicitud']

class AdopcionCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear adopciones"""
    class Meta:
        model = Adopcion
        fields = ['idMascota', 'idPropietario', 'Motivo_Adopción', 'Lugar_Vivienda', 
                  'Fecha_Adopción', 'Fecha_Entrega', 'Info_Mascota', 'Estado_Salud_Mascota']

    def create(self, validated_data):
        validated_data['Estado'] = 'Pendiente'
        validated_data['Fecha_Solicitud'] = now().date()
        validated_data['Estado_Solicitud'] = 'En revisión'
        validated_data['Estado_Ingreso_Mascota'] = ''
        validated_data['Control_Adopción'] = ''
        validated_data['Devolución'] = ''
        return super().create(validated_data)

# Mantener compatibilidad con código antiguo
class MascotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mascota
        fields = ['idMascota', 'Nombre_Mascota', 'Fecha_Nacimiento', 
                  'Raza', 'Genero', 'Peso', 'Especie', 'Color', 
                  'Tamaño', 'Origen', 'Tipo_Alimentación', 'Vacunas', 
                  'Esterilizado', 'Socializado', 'Estado_Salud']
        read_only_fields = ['idMascota']


class AdopcionSerializer(serializers.ModelSerializer):
    idMascota = MascotaSerializer(read_only=True)
    
    class Meta:
        model = Adopcion
        fields = ['idAdopcion', 'idPropietario', 'idMascota', 'idCriador',
                  'Estado', 'Fecha_Solicitud', 'Fecha_Adopción', 
                  'Motivo_Adopción', 'Estado_Solicitud', 'Fuente_Mascota']
        read_only_fields = ['idAdopcion', 'idMascota']


class CalificacionSerializer(serializers.ModelSerializer):
    """Serializador para calificaciones"""
    usuario_califica_nombre = serializers.CharField(source='usuario_califica.nombre', read_only=True)
    usuario_calificado_nombre = serializers.CharField(source='usuario_calificado.nombre', read_only=True)
    mascota_nombre = serializers.CharField(source='adopcion.idMascota.Nombre_Mascota', read_only=True)
    
    class Meta:
        model = Calificacion
        fields = ['idCalificacion', 'adopcion', 'usuario_califica', 'usuario_calificado', 
                  'usuario_califica_nombre', 'usuario_calificado_nombre', 'mascota_nombre',
                  'puntuacion', 'comentario', 'fecha_creacion']
        read_only_fields = ['idCalificacion', 'fecha_creacion']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializador para mensajes de chat"""
    remitente_nombre = serializers.CharField(source='remitente.nombre', read_only=True)
    receptor_nombre = serializers.CharField(source='receptor.nombre', read_only=True)
    receptor_id = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), write_only=True, source='receptor')

    class Meta:
        model = ChatMessage
        fields = ['idChat', 'remitente', 'remitente_nombre', 'receptor', 'receptor_nombre', 'receptor_id', 'mensaje', 'timestamp', 'leido']
        read_only_fields = ['idChat', 'remitente', 'remitente_nombre', 'receptor', 'receptor_nombre', 'timestamp', 'leido']


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializador para notificaciones"""
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = ['idNotificacion', 'usuario', 'usuario_nombre', 'tipo', 'titulo', 
                  'mensaje', 'leido', 'fecha_creacion', 'relacionado_con', 'adopcion', 'enlace_accion']
        read_only_fields = ['idNotificacion', 'fecha_creacion']


class NotificacionDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para notificaciones con informacion de adopcion y mascota"""
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    mascota_nombre = serializers.CharField(source='adopcion.idMascota.Nombre_Mascota', read_only=True, allow_null=True)
    mascota_foto = serializers.CharField(source='adopcion.idMascota.foto_mascota', read_only=True, allow_null=True)
    mascota_raza = serializers.CharField(source='adopcion.idMascota.Raza', read_only=True, allow_null=True)
    estado_adopcion = serializers.CharField(source='adopcion.Estado', read_only=True, allow_null=True)
    motivo_rechazo = serializers.CharField(source='adopcion.Motivo_Rechazo', read_only=True, allow_null=True)
    
    class Meta:
        model = Notificacion
        fields = ['idNotificacion', 'usuario', 'usuario_nombre', 'tipo', 'titulo', 
                  'mensaje', 'leido', 'fecha_creacion', 'relacionado_con', 'adopcion', 
                  'enlace_accion', 'mascota_nombre', 'mascota_foto', 'mascota_raza', 
                  'estado_adopcion', 'motivo_rechazo']
        read_only_fields = ['idNotificacion', 'fecha_creacion']
