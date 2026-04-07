from django.db.models import Q
from adopcion.models import Notificacion, Adopcion
from .models import Usuario


def nav_notifications(request):
    unread_notifications_count = 0
    chat_available = False
    if request.user.is_authenticated:
        unread_notifications_count = Notificacion.objects.filter(usuario=request.user, leido=False).count()
        if request.user.tipo == 'Propietario':
            criador_ids = Adopcion.objects.filter(idPropietario=request.user.idUsuario).values_list('idCriador', flat=True).distinct()
            chat_available = Usuario.objects.filter(idUsuario__in=[c for c in criador_ids if c]).exclude(idUsuario=request.user.idUsuario).exists()
        elif request.user.tipo == 'Criador':
            propietario_ids = Adopcion.objects.filter(idCriador=request.user.idUsuario).values_list('idPropietario', flat=True).distinct()
            chat_available = Usuario.objects.filter(idUsuario__in=[p for p in propietario_ids if p]).exclude(idUsuario=request.user.idUsuario).exists()
        else:
            chat_available = True

    return {
        'unread_notifications_count': unread_notifications_count,
        'chat_available': chat_available,
    }
