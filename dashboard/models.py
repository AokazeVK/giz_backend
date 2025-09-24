from django.db import models
from preparacion.models import Empresa # Asegúrate de que esta sea la ruta correcta a tu modelo Empresa

class Departamento(models.Model):
    """
    Modelo para representar un departamento dentro de una empresa.
    """
    nombre = models.CharField(max_length=100)
    
    # Un Departamento pertenece a una sola Empresa (N a 1)
    # on_delete=models.CASCADE asegura que si una Empresa se elimina,
    # todos sus departamentos también se eliminarán.
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.SET_NULL, 
        related_name='departamentos',
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre})"
