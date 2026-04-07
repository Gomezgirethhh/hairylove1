#!/usr/bin/env python
"""
Script para crear usuarios administradores en Hairylove.
Este script está diseñado para ser ejecutado desde manage.py shell.

Uso:
    python manage.py shell < crear_administrador.py
    
O dentro de Python shell:
    exec(open('crear_administrador.py').read())
"""

from usuarios.models import Usuario, Administrador
from django.contrib.auth.hashers import make_password

def crear_administrador():
    """Crear un nuevo usuario administrador"""
    
    print("\n" + "="*50)
    print("CREAR NUEVO ADMINISTRADOR - HAIRYLOVE")
    print("="*50 + "\n")
    
    # Pedir datos
    username = input("Nombre de usuario (para login): ").strip()
    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    correo = input("Email: ").strip()
    telefono = input("Teléfono: ").strip()
    password = input("Contraseña: ").strip()
    
    # Verificar si el usuario ya existe
    if Usuario.objects.filter(username=username).exists():
        print(f"\nError: El usuario '{username}' ya existe.")
        return
    
    if Usuario.objects.filter(correo=correo).exists():
        print(f"\nError: El email '{correo}' ya esta registrado.")
        return
    
    try:
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
        
        # Crear perfil de administrador
        es_superadmin = input("\n¿Es superadministrador? (s/n): ").lower() == 's'
        administrador = Administrador.objects.create(
            user=usuario,
            es_superadmin=es_superadmin
        )
        
        print("\n" + "="*50)
        print("\nAdministrador creado exitosamente.")
        print("="*50)
        print(f"Usuario: {username}")
        print(f"Nombre: {nombre} {apellido}")
        print(f"Email: {correo}")
        print(f"Tipo: {'Superadministrador' if es_superadmin else 'Administrador'}")
        print(f"ID: {usuario.idUsuario}")
        print(f"Fecha Creación: {administrador.fecha_creacion}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\nError al crear administrador: {str(e)}\n")

if __name__ == "__main__":
    crear_administrador()
