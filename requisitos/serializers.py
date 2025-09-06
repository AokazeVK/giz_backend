from rest_framework import serializers
from .models import TipoSello, Requisito, RequisitoInput, ChecklistEvaluacion, Evaluacion
from accounts.serializers import UserSerializer
from accounts.models import User

class RequisitoInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitoInput
        fields = ["id", "label", "input_type", "is_required", "requisito"]


class RequisitoSerializer(serializers.ModelSerializer):
    inputs = RequisitoInputSerializer(many=True, read_only=True)
    inputs_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Requisito
        fields = ["id", "tipoSello", "gestion", "is_active", "inputs", "inputs_data"]
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
            instance.inputs.all().delete() # Eliminar y recrear, más simple para bulk_create
            RequisitoInput.objects.bulk_create([
                RequisitoInput(requisito=instance, **data) for data in inputs_data
            ])
        return instance


class TipoSelloSerializer(serializers.ModelSerializer):
    requisitos = RequisitoSerializer(many=True, read_only=True)
    evaluaciones = serializers.SerializerMethodField()

    class Meta:
        model = TipoSello
        fields = ["id", "nombre", "descripcion", "is_active", "requisitos", "evaluaciones"]
        
    def get_evaluaciones(self, obj):
        gestion = self.context.get("gestion") # Obtener la gestión del contexto
        if gestion:
            evaluaciones = obj.evaluaciones.filter(gestion=gestion)
        else:
            evaluaciones = obj.evaluaciones.all()
        return EvaluacionSerializer(evaluaciones, many=True).data


class ChecklistEvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistEvaluacion
        fields = ["id", "nombre", "descripcion", "porcentaje", "is_active"]


class EvaluacionSerializer(serializers.ModelSerializer):
    evaluadores = UserSerializer(many=True, read_only=True)
    evaluadores_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__name='Evaluador'), # Asegura que solo se puedan asignar evaluadores
        many=True,
        write_only=True,
        required=False
    )
    checklist_evaluacion = ChecklistEvaluacionSerializer(many=True, read_only=True)
    checklist_ids = serializers.PrimaryKeyRelatedField(
        queryset=ChecklistEvaluacion.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Evaluacion
        fields = [
            "id", "tipoSello", "fecha_inicio", "fecha_fin", "gestion", 
            "evaluadores", "evaluadores_ids", "estado", 
            "checklist_evaluacion", "checklist_ids",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "estado", "created_at", "updated_at"]
        
    def create(self, validated_data):
        evaluadores_ids = validated_data.pop("evaluadores_ids", [])
        checklist_ids = validated_data.pop("checklist_ids", [])
        
        # Remove the gestion logic from here. The viewset will handle it.
        # It's also passed from the request body
        evaluacion = Evaluacion.objects.create(**validated_data) 
        
        if evaluadores_ids:
            evaluacion.evaluadores.set(evaluadores_ids)
        if checklist_ids:
            evaluacion.checklist_evaluacion.set(checklist_ids)
        
        return evaluacion

    def update(self, instance, validated_data):
        evaluadores_ids = validated_data.pop("evaluadores_ids", None)
        checklist_ids = validated_data.pop("checklist_ids", None)
        
        instance = super().update(instance, validated_data)
        
        if evaluadores_ids is not None:
            instance.evaluadores.set(evaluadores_ids)
        if checklist_ids is not None:
            instance.checklist_evaluacion.set(checklist_ids)
            
        return instance