# apps/preparacion/models.py
from django.db import models
from auditlog.registry import auditlog
from requisitos.models import TipoSello
from accounts.models import User


# ============================
#   EMPRESA
# ============================
class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    matricula = models.CharField(max_length=100, unique=True)
    nit = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=100)
    direccion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Nuevo campo para aprobación
    isAproved = models.BooleanField(default=True)

    # Relación 1 a N con TipoSello
    tipoSello = models.ForeignKey(
        TipoSello,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas"
    )

    # Nueva relación N a N con Capacitaciones y Asesoramientos
    capacitaciones = models.ManyToManyField(
        "Capacitacion", related_name="empresas", blank=True
    )
    asesoramientos = models.ManyToManyField(
        "Asesoramiento", related_name="empresas", blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.nit})"


auditlog.register(Empresa)


# ============================
#   CAPACITACION
# ============================
class Capacitacion(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    foto = models.ImageField(upload_to="capacitaciones/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

auditlog.register(Capacitacion)


# ============================
#   ASESORAMIENTO
# ============================
class Asesoramiento(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    foto = models.ImageField(upload_to="asesoramientos/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


auditlog.register(Asesoramiento)


# ============================
#   FASE EMPRESA
# ============================
class FaseEmpresa(models.Model):
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="fases_empresa"
    )
    fase_numero = models.IntegerField(
        default=1, help_text="Número que representa la fase actual de la empresa."
    )
    # Nuevo campo para registrar al evaluador que cambió la fase
    evaluador = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fases_empresa_asignadas"
    )
    gestion = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.empresa.nombre} - Fase {self.fase_numero} ({self.gestion})"



auditlog.register(FaseEmpresa)


# ============================
#   SOLICITUD DE ASESORAMIENTO
# ============================
class SolicitudAsesoramiento(models.Model):
    ESTADOS = [
        ("SOLICITADO", "Solicitado"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
        ("COMPLETADO", "Completado"),
        ("CANCELADO", "Cancelado"),
    ]

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="solicitudes_asesoramiento"
    )
    asesoramiento = models.ForeignKey(
        Asesoramiento, on_delete=models.CASCADE, related_name="solicitudes"
    )
    nombreAsesoramiento = models.CharField(max_length=255)
    fechaTentativaInicial = models.DateField()
    fechaTentativaFinal = models.DateField()
    fechaAprobada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="SOLICITADO")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.empresa.nombre} - {self.nombreAsesoramiento} ({self.estado})"


auditlog.register(SolicitudAsesoramiento)



# ============================
#   ARCHIVOS ASESORAMIENTO
# ============================
class ArchivoAsesoramiento(models.Model):
    asesoramiento = models.ForeignKey(
        "Asesoramiento", on_delete=models.CASCADE, related_name="archivos"
    )
    nombre = models.CharField(max_length=255)
    file = models.FileField(upload_to="asesoramientos/files/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.nombre} - {self.asesoramiento.nombre}"

auditlog.register(ArchivoAsesoramiento)

# ============================
#   ENCARGADOS ASESORAMIENTO
# ============================
class EncargadoAsesoramiento(models.Model):
    asesoramiento = models.ForeignKey(
        "Asesoramiento", on_delete=models.CASCADE, related_name="encargados_asesoramiento"
    )
    nombre = models.CharField(max_length=200)
    cargo = models.CharField(max_length=150, blank=True, null=True)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asesoramiento.nombre} - {self.encargado.nombre if self.encargado else 'Sin Encargado'}"

auditlog.register(EncargadoAsesoramiento)



class PublicacionEmpresaComunidad(models.Model):
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="publicaciones_comunidad"
    )
    titulo = models.CharField(max_length=255)
    fotourl = models.URLField(null=True, blank=True)   # si querés subir archivo, cambiar a ImageField
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.empresa.nombre} - {self.titulo}"

# registrar para auditlog
auditlog.register(PublicacionEmpresaComunidad)
