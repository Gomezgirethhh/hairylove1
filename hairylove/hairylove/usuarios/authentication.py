import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import Usuario


class JWTAuthentication(authentication.BaseAuthentication):
    """Autenticación JWT personalizada para la API."""
    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Token JWT no proporcionado')
        if len(auth_header) > 2:
            raise exceptions.AuthenticationFailed('Token JWT mal formado')

        try:
            token = auth_header[1].decode('utf-8')
        except UnicodeError:
            raise exceptions.AuthenticationFailed('Token JWT inválido')

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expirado')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Token inválido')

        if payload.get('token_type') != 'access':
            raise exceptions.AuthenticationFailed('Token JWT no válido para acceso')

        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('Token JWT inválido')

        try:
            user = Usuario.objects.get(idUsuario=user_id)
        except Usuario.DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuario no encontrado')

        if not getattr(user, 'is_active', True):
            raise exceptions.AuthenticationFailed('Usuario inactivo')

        return (user, token)

    def authenticate_header(self, request):
        return self.keyword
