#!/usr/bin/env python
import os
import sys
import django

# Add the Django project directory to the path
sys.path.insert(0, r'c:\Users\ANYELO\Desktop\hairylove\hairylove')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hairylove.settings')
os.chdir(r'c:\Users\ANYELO\Desktop\hairylove\hairylove')
django.setup()

from django.test import Client
from django.urls import reverse

# Test main page
client = Client()
response = client.get('/')
print(f"Response status code: {response.status_code}")

# Check if template is rendering correctly
if response.status_code == 200:
    content = response.content.decode('utf-8')
    # Check if the link contains the correct URL
    if 'href="/"' in content and '>Inicio<' in content:
        print("✓ Link ''Inicio'' found with href='/' attribute")
    else:
        print("✗ Link mismatch - checking content...")
        # Search for the nav-links section
        if '<a href="/"' in content:
            print("  - Found: <a href=\"/\"")
        if 'Inicio' in content:
            print("  - Found text: Inicio")
        # Find the actual href for Inicio
        import re
        inicio_match = re.search(r'<a href="([^"]*)"[^>]*>\s*(?:<i[^>]*></i>\s*)?Inicio', content)
        if inicio_match:
            print(f"  - Actual href for Inicio: {inicio_match.group(1)}")
else:
    print(f"Error: Response status code {response.status_code}")
