from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from auditlog.registry import auditlog
from accounts.models import User
from django.utils import timezone

# Tipos de datos para los inputs de los requisitos
INPUT_TYPES = (
    ("text", "Texto"),
    ("number", "Número"),
    ("date", "Fecha"),
    ("file", "Archivo"),
)

class TipoSello(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

auditlog.register(TipoSello)

class Requisito(models.Model):
    tipoSello = models.ForeignKey(
        TipoSello, on_delete=models.CASCADE, related_name="requisitos"
    )
    gestion = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tipoSello", "gestion", "nombre")

    def __str__(self):
        return f"{self.nombre} ({self.tipoSello.nombre} - {self.gestion})"

auditlog.register(Requisito)

class RequisitoInput(models.Model):
    requisito = models.ForeignKey(
        Requisito, on_delete=models.CASCADE, related_name="inputs"
    )
    label = models.CharField(max_length=100)
    input_type = models.CharField(max_length=10, choices=INPUT_TYPES)
    is_required = models.BooleanField(default=False)
    # Nuevo campo 'is_active'
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.label} ({self.get_input_type_display()})"

auditlog.register(RequisitoInput)

class Evaluacion(models.Model):
    ESTADO_CHOICES = (
        ("NOTIFICADO", "Notificado"),
        ("EN_CURSO", "En curso"),
        ("FINALIZADO", "Finalizado"),
    )

    tipoSello = models.ForeignKey(
        TipoSello, on_delete=models.CASCADE, related_name="evaluaciones"
    )
    # Relación uno a uno con Empresa (opcional, para una evaluación por empresa)
    empresa = models.OneToOneField(
        "preparacion.Empresa", on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluacion_asignada"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    gestion = models.CharField(max_length=10)
    
    # N a N con usuarios con rol de evaluador
    evaluadores = models.ManyToManyField(
        User,
        related_name="evaluaciones_asignadas",
        limit_choices_to={'role__name': 'Evaluador'}
    )
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="NOTIFICADO")
    # Nuevo campo 'is_active'
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        # Restricción: Una sola evaluación por tipo de sello y gestión
        unique_together = ('tipoSello', 'gestion')

    def __str__(self):
        return f"Evaluación de {self.tipoSello.nombre} - {self.gestion}"

auditlog.register(Evaluacion)

# Nuevo modelo para las fases de la evaluación
class EvaluacionFases(models.Model):
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE, related_name="fases"
    )
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    gestion = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Fase de Evaluación"
        verbose_name_plural = "Fases de Evaluación"

    def __str__(self):
        return f"{self.nombre} ({self.evaluacion.tipoSello.nombre})"

auditlog.register(EvaluacionFases)

# Modificar el modelo ChecklistEvaluacion para que apunte a EvaluacionFases
class ChecklistEvaluacion(models.Model):
    # Cambia la relación a EvaluacionFases
    evaluacion_fase = models.ForeignKey(
    EvaluacionFases, on_delete=models.CASCADE, related_name="checklists",
    null=True, blank=True
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre

auditlog.register(ChecklistEvaluacion)
