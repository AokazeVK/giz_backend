from rest_framework import serializers
# Importa los nuevos modelos
from .models import RequisitoInputValor, TipoSello, Requisito, RequisitoInput, ChecklistEvaluacion, Evaluacion, EvaluacionFases
from accounts.serializers import UserSerializer
from accounts.models import User
from django.db.models import Max

# Serializador para los Inputs de Requisitos
class RequisitoInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitoInput
        # Agrega el campo 'is_active'
        fields = ["id", "label", "input_type", "is_required", "is_active", "requisito"]
        read_only_fields = ["id"]


# Serializador para Requisitos
class RequisitoSerializer(serializers.ModelSerializer):
    inputs = RequisitoInputSerializer(many=True, read_only=True)
    inputs_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Requisito
        fields = ["id", "tipoSello", "gestion", "nombre", "descripcion", "is_active", "inputs", "inputs_data"]
        read_only_fields = ["id", "is_active"]
        
    def create(self, validated_data):
        inputs_data = validated_data.pop("inputs_data", [])
        requisito = Requisito.objects.create(**validated_data)
        if inputs_data:
            RequisitoInput.objects.bulk_create([
                RequisitoInput(requisito=requisito, **data) for data in inputs_data
            ])
        return requisito

    def update(self, instance, validated_data):
        inputs_data = validated_data.pop("inputs_data", None)
        instance = super().update(instance, validated_data)
        if inputs_data is not None:
            instance.inputs.all().delete()
            RequisitoInput.objects.bulk_create([
                RequisitoInput(requisito=instance, **data) for data in inputs_data
            ])
        return instance


# Serializador para Tipos de Sello
class TipoSelloSerializer(serializers.ModelSerializer):
    requisitos = RequisitoSerializer(many=True, read_only=True)
    evaluaciones = serializers.SerializerMethodField()

    class Meta:
        model = TipoSello
        fields = ["id", "nombre", "descripcion", "is_active", "requisitos", "evaluaciones"]
        
    def get_evaluaciones(self, obj):
        gestion = self.context.get("gestion")
        if gestion:
            evaluaciones = obj.evaluaciones.filter(gestion=gestion)
        else:
            evaluaciones = obj.evaluaciones.all()
        return EvaluacionSerializer(evaluaciones, many=True).data

class TipoSelloSerializerWithoutAllRelations(serializers.ModelSerializer):
     class Meta:
        model = TipoSello
        fields = ["id", "nombre","is_active"]

# Serializador para Checklists de Evaluación (ahora anidado en Fases)
class ChecklistEvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistEvaluacion
        # Agrega 'is_active' y el nuevo campo de relación
        fields = ["id", "nombre", "descripcion", "porcentaje", "is_active", "evaluacion_fase"]


# Serializador para las Fases de la Evaluación
class EvaluacionFasesSerializer(serializers.ModelSerializer):
    checklists = ChecklistEvaluacionSerializer(many=True, read_only=True)
    checklist_ids = serializers.PrimaryKeyRelatedField(
        queryset=ChecklistEvaluacion.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = EvaluacionFases
        # 'evaluacion' ahora puede ser escrito. 'gestion' sigue siendo solo de lectura
        fields = ["id", "nombre", "fecha_inicio", "fecha_fin", "evaluacion", "gestion", "is_active", "checklists", "checklist_ids"]
        read_only_fields = ["id", "gestion", "is_active"]
        
    def create(self, validated_data):
        checklist_ids = validated_data.pop("checklist_ids", [])
        # 'evaluacion' se recibe del request y se usa para crear la fase
        evaluacion_fase = EvaluacionFases.objects.create(**validated_data)
        if checklist_ids:
            for checklist in ChecklistEvaluacion.objects.filter(id__in=checklist_ids):
                checklist.evaluacion_fase = evaluacion_fase
                checklist.save()
        return evaluacion_fase
    
    def update(self, instance, validated_data):
        checklist_ids = validated_data.pop("checklist_ids", None)
        instance = super().update(instance, validated_data)
        if checklist_ids is not None:
            # Desasocia los antiguos checklists
            ChecklistEvaluacion.objects.filter(evaluacion_fase=instance).update(evaluacion_fase=None)
            # Asocia los nuevos
            for checklist in ChecklistEvaluacion.objects.filter(id__in=checklist_ids):
                checklist.evaluacion_fase = instance
                checklist.save()
        return instance


# Serializador para la Evaluación
# Serializador para la Evaluación
class EvaluacionSerializer(serializers.ModelSerializer):
    # Nuevo campo para mostrar el nombre del tipo de sello
    tipoSello_nombre = serializers.CharField(source='tipoSello.nombre', read_only=True)
    evaluadores = UserSerializer(many=True, read_only=True)
    evaluadores_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__name='Evaluador'),
        many=True,
        write_only=True,
        required=False
    )
    # Ahora la evaluación tiene fases, no checklists
    fases = EvaluacionFasesSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluacion
        # Agrega el campo 'is_active' y quita la relación directa con los checklists
        fields = [
            "id", "tipoSello", "tipoSello_nombre", "empresa", "fecha_inicio", "fecha_fin", "gestion", 
            "evaluadores", "evaluadores_ids", "estado", "is_active",
            "fases", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "estado", "is_active", "created_at", "updated_at", "tipoSello_nombre"]
        
    def create(self, validated_data):
        evaluadores_ids = validated_data.pop("evaluadores_ids", [])
        
        # 'gestion' ya viene en validated_data, no hay que sacarla
        evaluacion = Evaluacion.objects.create(**validated_data) 
        
        if evaluadores_ids:
            evaluacion.evaluadores.set(evaluadores_ids)
        
        return evaluacion

    def update(self, instance, validated_data):
        evaluadores_ids = validated_data.pop("evaluadores_ids", None)
        
        instance = super().update(instance, validated_data)
        
        if evaluadores_ids is not None:
            instance.evaluadores.set(evaluadores_ids)
            
        return instance


class RequisitoInputValorSerializer(serializers.ModelSerializer):
    archivo_url = serializers.SerializerMethodField()
    requisito_input_nombre = serializers.CharField(source="requisito_input.label", read_only=True)
    class Meta:
        model = RequisitoInputValor
        fields = ["id", "requisito_input", "requisito_input_nombre", "valor", "archivo", "archivo_url", "created_at"]

    from django.db.models import Max


    def get_archivo_url(self, obj):
        request = self.context.get("request")
        if obj.archivo and request:
            return request.build_absolute_uri(obj.archivo.url)
        return None

    def validate(self, data):
        requisito_input = data["requisito_input"]

        # Validación de required
        if requisito_input.is_required:
            if requisito_input.input_type == "file":
                if not data.get("archivo"):
                    raise serializers.ValidationError("Este archivo es obligatorio.")
            else:
                if not data.get("valor"):
                    raise serializers.ValidationError("Este campo es obligatorio.")

        return data