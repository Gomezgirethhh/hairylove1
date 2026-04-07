#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hairylove.settings')
django.setup()

from django.urls import reverse

# Verificar que 'index' se resuelve
try:
    url = reverse('index')
    print(f"✓ 'index' resuelve a: {url}")
except Exception as e:
    print(f"✗ Error resolviendo 'index': {e}")

# Verificar otras URLs importantes
urls_to_check = ['mascotas_adopcion', 'propietario', 'criador', 'chat_lista', 'notificaciones']
for url_name in urls_to_check:
    try:
        url = reverse(url_name)
        print(f"✓ '{url_name}' resuelve a: {url}")
    except Exception as e:
        print(f"✗ Error resolviendo '{url_name}': {e}")
