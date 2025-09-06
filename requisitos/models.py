from django.db import models
from auditlog.registry import auditlog
from accounts.models import User

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
    gestion = models.CharField(max_length=10) # Se llena desde la cookie "gestion"
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        # Esto asegura que no haya dos requisitos con el mismo nombre
        # para un mismo tipo de sello en la misma gestión.
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
    
    def __str__(self):
        return f"{self.label} ({self.get_input_type_display()})"

auditlog.register(RequisitoInput)


class ChecklistEvaluacion(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

auditlog.register(ChecklistEvaluacion)


class Evaluacion(models.Model):
    ESTADO_CHOICES = (
        ("NOTIFICADO", "Notificado"),
        ("EN_CURSO", "En curso"),
        ("FINALIZADO", "Finalizado"),
    )

    tipoSello = models.ForeignKey(
        TipoSello, on_delete=models.CASCADE, related_name="evaluaciones"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    gestion = models.CharField(max_length=10)
    
    # N a N con usuarios con rol de evaluador
    evaluadores = models.ManyToManyField(
        User,
        related_name="evaluaciones_asignadas",
        limit_choices_to={'role__name': 'Evaluador'} # O el nombre de tu rol de evaluador
    )
    
    # N a N con ChecklistEvaluacion
    checklist_evaluacion = models.ManyToManyField(
        ChecklistEvaluacion,
        related_name="evaluaciones"
    )
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="NOTIFICADO")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Evaluación de {self.tipoSello.nombre} - {self.gestion}"

auditlog.register(Evaluacion)