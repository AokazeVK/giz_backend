from django.db import models
from auditlog.registry import auditlog
from django.utils import timezone

class Evento(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    lugar = models.CharField(max_length=255)
    
    # Se cambian a campos separados para Fecha y Hora
    fecha = models.DateField()
    hora = models.TimeField()
    
    is_active = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='eventos/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

auditlog.register(Evento)
