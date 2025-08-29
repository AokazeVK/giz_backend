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

auditlog.register(Ministerio)
auditlog.register(Encargado)
