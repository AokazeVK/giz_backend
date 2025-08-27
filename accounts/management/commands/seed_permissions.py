from django.core.management.base import BaseCommand
from accounts.models import Permission

TREE = {
    "label": "Permisos", "code": "permisos", "children": [
        {
            "label": "Usuarios", "code": "usuarios", "children": [
                {"label": "Crear Usuarios", "code": "crear_usuarios"},
                {"label": "Editar Usuarios", "code": "editar_usuarios"},
                {"label": "Eliminar Usuarios", "code": "eliminar_usuarios"},
                {"label": "Listar Usuarios", "code": "listar_usuarios"},
                {"label": "Cambiar Contraseña Usuarios", "code": "cambiar_contrasena_usuarios"},
            ]
        },
        {
            "label": "Roles", "code": "roles", "children": [
                {"label": "Crear Roles", "code": "crear_roles"},
                {"label": "Editar Roles", "code": "editar_roles"},
                {"label": "Eliminar Roles", "code": "eliminar_roles"},
                {"label": "Listar Roles", "code": "listar_roles"},
                {"label": "Editar Permisos Rol", "code": "editar_permisos_roles"},
            ]
        },
        {
            "label": "Auditoría", "code": "auditoria", "children": [
                {"label": "Ver Historial Global", "code": "ver_historial_global"},
            ]
        }
    ]
}

def upsert(node, parent=None):
    obj, _ = Permission.objects.get_or_create(code=node["code"], defaults={"label": node["label"], "parent": parent})
    if obj.label != node["label"] or obj.parent_id != (parent.id if parent else None):
        obj.label = node["label"]
        obj.parent = parent
        obj.save()
    for child in node.get("children", []):
        upsert(child, obj)

class Command(BaseCommand):
    help = "Crea/actualiza permisos base en árbol"

    def handle(self, *args, **options):
        upsert(TREE, None)
        self.stdout.write(self.style.SUCCESS("Permisos base creados/actualizados."))
