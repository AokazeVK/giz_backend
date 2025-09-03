# giz_backend/celery.py

import os
from celery import Celery

# Establece el módulo de configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "giz_backend.settings")

# Crea una instancia de la aplicación Celery
app = Celery("giz_backend")

# Carga la configuración de Celery desde el archivo settings.py de Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descubre y registra automáticamente las tareas en todas las apps de Django
app.autodiscover_tasks()