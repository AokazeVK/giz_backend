from django.db import models
from auditlog.registry import auditlog

class Curso(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    visualizaciones = models.PositiveIntegerField(default=0)
    foto = models.ImageField(upload_to="cursos/fotos/")
    link_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

# Registrar el modelo en auditlog
auditlog.register(Curso)