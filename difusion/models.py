# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from auditlog.registry import auditlog



class Ministerio(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    direccion = models.CharField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=True)  # toggle activar/desactivar

    def __str__(self):
        return self.nombre


class Encargado(models.Model):
    ministerio = models.ForeignKey(Ministerio, on_delete=models.CASCADE, related_name="encargados")
    nombre = models.CharField(max_length=200)
    cargo = models.CharField(max_length=150, blank=True, null=True)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)  # toggle activar/desactivar

    def __str__(self):
        return f"{self.nombre} - {self.ministerio.nombre}"
    
class Convocatoria(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class FechaConvocatoria(models.Model):
    convocatoria = models.ForeignKey(
        Convocatoria, on_delete=models.CASCADE, related_name="fechas"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    gestion = models.CharField(max_length=10)  # ej "2025"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.convocatoria.nombre} ({self.gestion}) {self.fecha_inicio} - {self.fecha_fin}"


class ArchivoFechaConvocatoria(models.Model):
    fecha_convocatoria = models.ForeignKey(
        FechaConvocatoria, on_delete=models.CASCADE, related_name="archivos"
    )
    nombre = models.CharField(max_length=255)
    file = models.FileField(upload_to="convocatorias/files/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.nombre} - {self.fecha_convocatoria}"

auditlog.register(Convocatoria)
auditlog.register(FechaConvocatoria)
auditlog.register(ArchivoFechaConvocatoria)
auditlog.register(Ministerio)
auditlog.register(Encargado)
