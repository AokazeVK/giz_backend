# apps/preparacion/models.py
from django.db import models
from auditlog.registry import auditlog
from accounts.models import User
from requisitos.models import TipoSello

class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    matricula = models.CharField(max_length=100, unique=True)
    nit = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=100)
    direccion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Nuevo campo para aprobación
    isAproved = models.BooleanField(default=True)

    # Nueva relación 1 a N con TipoSello
    # 1 TipoSello puede tener N empresas, pero una empresa solo tiene 1 TipoSello
    tipoSello = models.ForeignKey(
        TipoSello,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.nit})"

auditlog.register(Empresa)