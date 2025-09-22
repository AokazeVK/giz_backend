from django.contrib import admin
from .models import Departamento

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa')
    search_fields = ('nombre', 'empresa__nombre')
