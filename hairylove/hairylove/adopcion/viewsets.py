from rest_framework import viewsets, permissions, status, filters, pagination
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.dateparse import parse_date
from datetime import datetime
import openpyxl
from django.db.models import Q
from usuarios.models import Criador, Usuario
from usuarios.serializers import UsuarioSerializer
from .models import Mascota, Adopcion, Calificacion, Notificacion, ChatMessage
from .serializers import (
    MascotaListSerializer, 
    MascotaDetailSerializer,
    AdopcionListSerializer, 
    AdopcionCreateSerializer,
    CalificacionSerializer,
    NotificacionSerializer,
    NotificacionDetailSerializer,
    ChatMessageSerializer,
)

class MascotaViewSet(viewsets.ModelViewSet):
    """
    API para gestionar mascotas.
    Endpoints disponibles:
    - GET /api/mascotas/ - Listar todas las mascotas
    - GET /api/mascotas/?especie=Perro - Filtrar por especie
    - GET /api/mascotas/?raza=Labrador - Filtrar por raza
    - GET /api/mascotas/{id}/ - Obtener detalle de una mascota
    - POST /api/mascotas/ - Crear nueva mascota (requiere autenticación)
    - PUT/PATCH /api/mascotas/{id}/ - Actualizar mascota
    - DELETE /api/mascotas/{id}/ - Eliminar mascota
    - GET /api/mascotas/por_especie/ - Obtener especies disponibles
    """
    queryset = Mascota.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['Especie', 'Raza', 'Genero', 'Estado_Salud', 'Esterilizado', 'Socializado']
    search_fields = ['Nombre_Mascota', 'Raza', 'Especie', 'Color']
    ordering_fields = ['Nombre_Mascota', 'Peso', 'Fecha_Nacimiento']
    
    def get_serializer_class(self):
        """Usar diferentes serializadores según la acción"""
        if self.action == 'retrieve':
            return MascotaDetailSerializer
        elif self.action == 'list':
            return MascotaListSerializer
        return MascotaDetailSerializer
    
    @action(detail=False, methods=['get'])
    def por_especie(self, request):
        """Obtener todas las especies disponibles con conteo"""
        from django.db.models import Count
        especies = Mascota.objects.values('Especie').annotate(cantidad=Count('idMascota')).order_by('Especie')
        return Response(especies)
    
    @action(detail=False, methods=['get'])
    def razas_por_especie(self, request):
        """Obtener razas disponibles para una especie"""
        from .razas import RAZAS_POR_ESPECIE
        especie = request.query_params.get('especie', None)
        
        if especie:
            razas = RAZAS_POR_ESPECIE.get(especie, [])
            return Response({'especie': especie, 'razas': razas})
        
        return Response(RAZAS_POR_ESPECIE)
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Obtener solo mascotas disponibles para adopción"""
        mascotas = self.filter_queryset(self.get_queryset())
        # Excluir mascotas que ya fueron adoptadas
        adoptadas = Adopcion.objects.filter(Estado='Aprobada').values_list('idMascota', flat=True)
        disponibles = mascotas.exclude(idMascota__in=adoptadas)
        
        serializer = self.get_serializer(disponibles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_excel(self, request):
        """Subir un archivo Excel para crear mascotas en lote."""
        if not request.user.is_authenticated:
            return Response({'error': 'Debes estar autenticado para usar este endpoint.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not hasattr(request.user, 'tipo') or request.user.tipo != 'Criador':
            return Response({'error': 'Solo los criadores pueden subir mascotas en lote.'}, status=status.HTTP_403_FORBIDDEN)

        archivo = request.FILES.get('archivo_excel') or request.FILES.get('file')
        if not archivo:
            return Response({'error': 'Se requiere un archivo Excel .xlsx'}, status=status.HTTP_400_BAD_REQUEST)

        if not archivo.name.lower().endswith('.xlsx'):
            return Response({'error': 'Solo se permiten archivos .xlsx'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workbook = openpyxl.load_workbook(archivo)
            worksheet = workbook.active
        except Exception as exc:
            return Response({'error': f'No se pudo leer el archivo Excel: {str(exc)}'}, status=status.HTTP_400_BAD_REQUEST)

        errores = []
        mascotas_creadas = []

        for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or all(cell is None for cell in row):
                continue

            try:
                nombre = row[0]
                fecha_nac = row[1]
                raza = row[2]
                genero = row[3]
                peso = row[4]
                especie = row[5]
                color = row[6]
                tamano = row[7]
                historial = row[8]
                tipo_alimentacion = row[9]
                enfermedades = row[10]
                vivienda = row[11]
                vacunas = row[12]
                compatibilidad = row[13]
                descripcion_fisica = row[14]

                if not nombre or not raza or not genero:
                    errores.append(f'Fila {row_num}: Nombre, raza y género son obligatorios')
                    continue

                if isinstance(fecha_nac, str):
                    fecha_nac = parse_date(fecha_nac)
                elif isinstance(fecha_nac, datetime):
                    fecha_nac = fecha_nac.date()

                if fecha_nac is None:
                    errores.append(f'Fila {row_num}: Fecha de nacimiento inválida o faltante')
                    continue

                mascota = Mascota.objects.create(
                    Nombre_Mascota=nombre,
                    Fecha_Nacimiento=fecha_nac,
                    Raza=raza,
                    Genero=genero,
                    Peso=float(peso) if peso else 0,
                    Especie=especie or 'Perro',
                    Color=color or '',
                    Tamaño=tamano or 'Mediano',
                    Historial_Mascota=historial or '',
                    Tipo_Alimentación=tipo_alimentacion or '',
                    Enfermedades=enfermedades or '',
                    Vivienda=vivienda or '',
                    Vacunas=vacunas or '',
                    Compatibilidad_Mascota=compatibilidad or '',
                    Descripción_Física=descripcion_fisica or '',
                    idCriador=request.user.idUsuario,
                    disponible=True
                )
                mascotas_creadas.append(mascota)
            except Exception as exc:
                errores.append(f'Fila {row_num}: {str(exc)}')

        serializer = self.get_serializer(mascotas_creadas, many=True)
        return Response({
            'creadas': len(mascotas_creadas),
            'errores': errores,
            'mascotas': serializer.data,
        }, status=status.HTTP_201_CREATED if mascotas_creadas else status.HTTP_400_BAD_REQUEST)


class AdopcionViewSet(viewsets.ModelViewSet):
    """
    API para gestionar adopciones.
    Endpoints disponibles:
    - GET /api/adopciones/ - Listar todas las adopciones
    - POST /api/adopciones/ - Crear nueva solicitud de adopción
    - GET /api/adopciones/{id}/ - Obtener detalle de adopción
    - PUT/PATCH /api/adopciones/{id}/ - Actualizar adopción
    - DELETE /api/adopciones/{id}/ - Eliminar adopción
    - GET /api/adopciones/mis-adopciones/ - Ver adopciones del usuario actual
    - GET /api/adopciones/pendientes/ - Ver adopciones pendientes (solo admin)
    """
    queryset = Adopcion.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['Estado', 'Estado_Solicitud', 'Fuente_Mascota']
    ordering_fields = ['Fecha_Solicitud', 'Fecha_Adopción']
    
    def get_serializer_class(self):
        """Usar diferentes serializadores según la acción"""
        if self.action == 'create':
            return AdopcionCreateSerializer
        return AdopcionListSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva solicitud de adopción"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def mis_adopciones(self, request):
        """Obtener las adopciones del usuario actual"""
        # Asumir que idPropietario está relacionado con el usuario actual
        adopciones = self.filter_queryset(self.get_queryset()).filter(idPropietario=request.user.idUsuario)
        serializer = self.get_serializer(adopciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pendientes(self, request):
        """Obtener adopciones pendientes (solo administradores)"""
        pendientes = self.filter_queryset(self.get_queryset()).filter(Estado='Pendiente')
        serializer = self.get_serializer(pendientes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprobar una solicitud de adopción (solo admin)"""
        if not request.user.is_staff:
            return Response({'error': 'No tienes permisos para aprobar adopciones'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        adopcion = self.get_object()
        adopcion.Estado = 'Aprobada'
        adopcion.Estado_Solicitud = 'Completada'
        adopcion.save()
        
        # Crear notificación para el propietario
        try:
            propietario = Usuario.objects.get(idUsuario=adopcion.idPropietario)
            Notificacion.objects.create(
                usuario=propietario,
                tipo='adopcion_aprobada',
                adopcion=adopcion,
                titulo=f'Tu solicitud de adopcion fue aprobada',
                mensaje=f'Tu solicitud para adoptar a {adopcion.idMascota.Nombre_Mascota} ha sido aprobada. Pronto podras recoger a tu nueva mascota.',
                enlace_accion=f'/adopcion/detalles/{adopcion.idAdopcion}/'
            )
        except Usuario.DoesNotExist:
            pass
        
        serializer = self.get_serializer(adopcion)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechazar una solicitud de adopción (solo admin)"""
        if not request.user.is_staff:
            return Response({'error': 'No tienes permisos para rechazar adopciones'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        motivo_rechazo = request.data.get('motivo_rechazo', 'No especificado')
        
        adopcion = self.get_object()
        adopcion.Estado = 'Rechazada'
        adopcion.Estado_Solicitud = 'Cancelada'
        adopcion.Motivo_Rechazo = motivo_rechazo
        adopcion.save()
        
        # Crear notificación para el propietario
        try:
            propietario = Usuario.objects.get(idUsuario=adopcion.idPropietario)
            Notificacion.objects.create(
                usuario=propietario,
                tipo='adopcion_rechazada',
                adopcion=adopcion,
                titulo=f'Tu solicitud de adopcion fue rechazada',
                mensaje=f'Tu solicitud para adoptar a {adopcion.idMascota.Nombre_Mascota} ha sido rechazada. Motivo: {motivo_rechazo}',
                enlace_accion=f'/adopcion/detalles/{adopcion.idAdopcion}/'
            )
        except Usuario.DoesNotExist:
            pass
        
        serializer = self.get_serializer(adopcion)
        return Response(serializer.data)


class CalificacionViewSet(viewsets.ModelViewSet):
    """
    API para gestionar calificaciones.
    Endpoints disponibles:
    - GET /api/calificaciones/ - Listar todas las calificaciones
    - GET /api/calificaciones/{id}/ - Obtener detalle
    - POST /api/calificaciones/ - Crear calificación
    - GET /api/calificaciones/recibidas/{usuario_id}/ - Calificaciones recibidas por un usuario
    - GET /api/calificaciones/dadas/{usuario_id}/ - Calificaciones dadas por un usuario
    """
    queryset = Calificacion.objects.all()
    serializer_class = CalificacionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['usuario_califica', 'usuario_calificado', 'puntuacion']
    ordering_fields = ['fecha_creacion', 'puntuacion']
    ordering = ['-fecha_creacion']
    
    @action(detail=False, methods=['get'])
    def recibidas(self, request):
        """Obtener calificaciones recibidas por un usuario"""
        usuario_id = request.query_params.get('usuario_id')
        if not usuario_id:
            return Response({'error': 'usuario_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        calificaciones = Calificacion.objects.filter(usuario_calificado_id=usuario_id).order_by('-fecha_creacion')
        serializer = self.get_serializer(calificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dadas(self, request):
        """Obtener calificaciones dadas por un usuario"""
        usuario_id = request.query_params.get('usuario_id')
        if not usuario_id:
            return Response({'error': 'usuario_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        calificaciones = Calificacion.objects.filter(usuario_califica_id=usuario_id).order_by('-fecha_creacion')
        serializer = self.get_serializer(calificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mis_calificaciones_dadas(self, request):
        """Obtener las calificaciones que el usuario actual ha dado"""
        if not request.user.is_authenticated:
            return Response({'error': 'Debes estar autenticado'}, status=status.HTTP_401_UNAUTHORIZED)
        
        calificaciones = Calificacion.objects.filter(usuario_califica=request.user).order_by('-fecha_creacion')
        serializer = self.get_serializer(calificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mis_calificaciones_recibidas(self, request):
        """Obtener las calificaciones que el usuario actual ha recibido"""
        if not request.user.is_authenticated:
            return Response({'error': 'Debes estar autenticado'}, status=status.HTTP_401_UNAUTHORIZED)
        
        calificaciones = Calificacion.objects.filter(usuario_calificado=request.user).order_by('-fecha_creacion')
        serializer = self.get_serializer(calificaciones, many=True)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """API para gestionar mensajes del chat entre usuarios."""
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['timestamp']
    ordering = ['timestamp']

    def get_queryset(self):
        usuario = self.request.user
        queryset = ChatMessage.objects.filter(Q(remitente=usuario) | Q(receptor=usuario)).order_by('timestamp')
        contacto_id = self.request.query_params.get('contacto_id')
        if contacto_id:
            queryset = queryset.filter(
                (Q(remitente=usuario) & Q(receptor_id=contacto_id)) |
                (Q(remitente_id=contacto_id) & Q(receptor=usuario))
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(remitente=self.request.user)

    @action(detail=False, methods=['get'])
    def conversaciones(self, request):
        usuario = request.user
        mensajes = ChatMessage.objects.filter(Q(remitente=usuario) | Q(receptor=usuario))
        contactos_ids = set()
        for mensaje in mensajes:
            if mensaje.remitente_id != usuario.idUsuario:
                contactos_ids.add(mensaje.remitente_id)
            if mensaje.receptor_id != usuario.idUsuario:
                contactos_ids.add(mensaje.receptor_id)

        contactos = Usuario.objects.filter(idUsuario__in=contactos_ids)
        serializer = UsuarioSerializer(contactos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def marcar_leido(self, request):
        contacto_id = request.data.get('contacto_id')
        if not contacto_id:
            return Response({'error': 'contacto_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        actualizados = ChatMessage.objects.filter(remitente_id=contacto_id, receptor=request.user, leido=False).update(leido=True)
        return Response({'mensajes_marcados': actualizados})


class NotificacionViewSet(viewsets.ModelViewSet):
    """
    API para gestionar notificaciones.
    Endpoints disponibles:
    - GET /api/notificaciones/ - Listar notificaciones del usuario
    - GET /api/notificaciones/{id}/ - Obtener detalle (marca como leída automáticamente)
    - PUT/PATCH /api/notificaciones/{id}/ - Actualizar notificación
    - GET /api/notificaciones/no_leidas/ - Obtener notificaciones no leídas
    - POST /api/notificaciones/marcar_todo_leido/ - Marcar todo como leído
    - POST /api/notificaciones/{id}/marcar_leido/ - Marcar una notificación como leída
    - GET /api/notificaciones/por_tipo/ - Filtrar por tipo
    """
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'leido']
    ordering_fields = ['fecha_creacion']
    ordering = ['-fecha_creacion']
    
    def get_queryset(self):
        """Retornar solo notificaciones del usuario actual"""
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')
    
    def get_serializer_class(self):
        """Usar diferentes serializadores según la acción"""
        if self.action == 'retrieve':
            return NotificacionDetailSerializer
        return NotificacionSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de notificación y marcar como leída automáticamente"""
        notificacion = self.get_object()
        # Marcar como leída automáticamente al acceder
        if not notificacion.leido:
            notificacion.leido = True
            notificacion.save()
        
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        """Obtener notificaciones no leídas del usuario"""
        notificaciones = Notificacion.objects.filter(usuario=request.user, leido=False).order_by('-fecha_creacion')
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reciente(self, request):
        """Obtener las 10 notificaciones más recientes"""
        notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:10]
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Obtener notificaciones filtradas por tipo específico"""
        tipo = request.query_params.get('tipo', None)
        if not tipo:
            return Response({'error': 'Parámetro "tipo" es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        notificaciones = Notificacion.objects.filter(usuario=request.user, tipo=tipo).order_by('-fecha_creacion')
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def marcar_todo_leido(self, request):
        """Marcar todas las notificaciones como leídas"""
        updated = Notificacion.objects.filter(usuario=request.user, leido=False).update(leido=True)
        return Response({
            'mensaje': f'{updated} notificación{"es" if updated != 1 else ""} marcada{"s" if updated != 1 else ""} como leída{"s" if updated != 1 else ""}'
        })
    
    @action(detail=True, methods=['post'])
    def marcar_leido(self, request, pk=None):
        """Marcar una notificación como leída"""
        notificacion = self.get_object()
        notificacion.leido = True
        notificacion.save()
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de notificaciones del usuario"""
        todas = Notificacion.objects.filter(usuario=request.user).count()
        no_leidas = Notificacion.objects.filter(usuario=request.user, leido=False).count()
        por_tipo = {}
        for tipo, _ in Notificacion.TIPO_CHOICES:
            por_tipo[tipo] = Notificacion.objects.filter(usuario=request.user, tipo=tipo).count()
        
        return Response({
            'total': todas,
            'no_leidas': no_leidas,
            'leidas': todas - no_leidas,
            'por_tipo': por_tipo
        })
