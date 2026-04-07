#!/usr/bin/env python
"""
Script para crear un usuario administrador en Hairylove
Uso: python manage.py shell < crear_admin.py
"""

from usuarios.models import Usuario, Administrador
from django.contrib.auth.hashers import make_password

# Datos del administrador
username = 'admin'
nombre = 'Administrador'
apellido = 'Hairylove'
correo = 'admin@hairylove.com'
telefono = '+5712345678'
password = 'admin123456'

# Verificar si ya existe
if Usuario.objects.filter(username=username).exists():
    print(f"El usuario '{username}' ya existe")
else:
    # Crear usuario
    usuario = Usuario.objects.create(
        username=username,
        nombre=nombre,
        apellido=apellido,
        correo=correo,
        telefono=telefono,
        tipo='Administrador',
        is_staff=True,
        is_superuser=True,
        password=make_password(password)
    )
    
    # Crear perfil administrador
    Administrador.objects.create(
        user=usuario,
        es_superadmin=True
    )
    
    print(f"Administrador creado exitosamente.")
    print(f"   Username: {username}")
    print(f"   Email: {correo}")
    print(f"   Password: {password}")
    print(f"\n   Acceder en: http://127.0.0.1:8000/login/")
