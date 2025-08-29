# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from auditlog.registry import auditlog
from PIL import Image
from io import BytesIO
from django.core.files import File

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # toggle activar/desactivar

    # ManyToMany real con tabla intermedia
    permissions = models.ManyToManyField(
        "Permission",
        through="RolePermission",
        related_name="roles",
        blank=True,
    )

    def __str__(self):
        return self.name


class Permission(models.Model):
    label = models.CharField(max_length=200)                        # Ej: "Crear Usuarios"
    code = models.CharField(max_length=100, unique=True, db_index=True)  # Ej: "crear_usuarios"
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")

    def __str__(self):
        return self.label


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("role", "permission")


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
            
        super().save(*args, **kwargs)

        if self.avatar:
            img = Image.open(self.avatar.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                
                # Guarda la imagen redimensionada
                img.save(self.avatar.path)

    def __str__(self):
        return self.email

class UserActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=200)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user_id} - {self.action} - {self.timestamp}"


# Auditlog registra cambios de modelos (alta/edición/baja) automáticamente
auditlog.register(User)
auditlog.register(Role)
auditlog.register(Permission)
