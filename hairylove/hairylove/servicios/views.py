from django.shortcuts import render
from rest_framework import viewsets, permissions, pagination, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Servicio, SolicitudServicio
from .serializers import ServicioSerializer, SolicitudServicioSerializer


# ==================== VISTAS TRADICIONALES ====================

def lista_servicios(request):
    """Página de lista de servicios disponibles."""
    servicios = Servicio.objects.all()
    return render(request, 'servicios/lista_servicios.html', {'servicios': servicios})


def servicios(request):
    servicios = Servicio.objects.all()
    return render(request, 'servicios/servicios.html', {'servicios': servicios})


# ==================== API VIEWSETS ====================

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_fields = ['especialista']
    search_fields = ['nombre_servicio', 'descripcion']
    ordering_fields = ['precio_base']
    ordering = ['precio_base']


class SolicitudServicioViewSet(viewsets.ModelViewSet):
    queryset = SolicitudServicio.objects.all()
    serializer_class = SolicitudServicioSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_fields = ['estado', 'servicio', 'usuario']
    ordering_fields = ['fecha_solicitud', 'fecha_programada', 'estado']

    def get_queryset(self):
        if self.request.user.is_staff:
            return SolicitudServicio.objects.all()
        return SolicitudServicio.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def mis_solicitudes(self, request):
        solicitudes = self.get_queryset()
        serializer = self.get_serializer(solicitudes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        solicitud = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Solo administradores pueden confirmar solicitudes'}, status=status.HTTP_403_FORBIDDEN)
        solicitud.estado = 'Confirmada'
        solicitud.save()
        serializer = self.get_serializer(solicitud)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        solicitud = self.get_object()
        if solicitud.usuario != request.user and not request.user.is_staff:
            return Response({'error': 'No tienes permisos para cancelar esta solicitud'}, status=status.HTTP_403_FORBIDDEN)
        solicitud.estado = 'Cancelada'
        solicitud.save()
        serializer = self.get_serializer(solicitud)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        solicitud = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Solo administradores pueden completar solicitudes'}, status=status.HTTP_403_FORBIDDEN)
        solicitud.estado = 'Completada'
        solicitud.save()
        serializer = self.get_serializer(solicitud)
        return Response(serializer.data)
