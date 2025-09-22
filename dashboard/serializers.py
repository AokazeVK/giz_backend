from rest_framework import serializers
from .models import Departamento

class DepartamentoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Departamento.
    """
    # Usamos CharField para mostrar el nombre de la empresa en lugar de su ID
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = Departamento
        fields = ['id', 'nombre', 'empresa', 'empresa_nombre']
        read_only_fields = ['id', 'empresa_nombre']
