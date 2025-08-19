from django.db import models
from django.contrib.auth.models import AbstractUser

# Modelo de Rol
class Role(models.Model):
    # 'id' se crea automáticamente
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

# Tu modelo de Usuario ya existente
class User(AbstractUser):
    email = models.EmailField(unique=True)
    
    # Nuevo campo para el rol
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email