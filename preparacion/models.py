from django.db import models
from auditlog.registry import auditlog
from accounts.models import User
# apps/preparacion/models.py
class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    matricula = models.CharField(max_length=100, unique=True)
    nit = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=100)
    direccion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # ¡Elimina la siguiente línea!
    # usuarios = models.ManyToManyField(User, related_name="empresas", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.nit})"

auditlog.register(Empresa)