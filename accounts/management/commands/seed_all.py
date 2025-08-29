# apps/accounts/management/commands/seed_all.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import Role, Permission

# Estructura de árbol con TODOS los permisos de las vistas
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
        },
        {
            "label": "Ministerios", "code": "ministerios", "children": [
                {"label": "Crear Ministerios", "code": "crear_ministerios"},
                {"label": "Editar Ministerios", "code": "editar_ministerios"},
                {"label": "Eliminar Ministerios", "code": "eliminar_ministerios"},
                {"label": "Listar Ministerios", "code": "listar_ministerios"},
            ]
        },
        {
            "label": "Encargados", "code": "encargados", "children": [
                {"label": "Crear Encargados", "code": "crear_encargados"},
                {"label": "Editar Encargados", "code": "editar_encargados"},
                {"label": "Eliminar Encargados", "code": "eliminar_encargados"},
                {"label": "Listar Encargados", "code": "listar_encargados"},
                {"label": "Listar Encargados por Ministerio", "code": "listar_encargados_por_ministerio"},
            ]
        },
    ]
}

def upsert_permissions(node, parent=None):
    obj, _ = Permission.objects.get_or_create(code=node["code"], defaults={"label": node["label"], "parent": parent})
    if obj.label != node["label"] or obj.parent_id != (parent.id if parent else None):
        obj.label = node["label"]
        obj.parent = parent
        obj.save()
    for child in node.get("children", []):
        upsert_permissions(child, obj)

class Command(BaseCommand):
    help = 'Crea/actualiza los permisos, el rol de Super Admin y un superusuario.'

    @transaction.atomic
    def handle(self, *args, **options):
        email = "admin@mail.com"
        password = "Hola1234"
        username = "superadmin"
        
        self.stdout.write(self.style.NOTICE('Iniciando el proceso de seeding...'))

        # 1. Crea/actualiza todos los permisos
        upsert_permissions(TREE, None)
        self.stdout.write(self.style.SUCCESS("Permisos base creados/actualizados exitosamente."))

        # 2. Crea o obtiene el rol de Super Administrador
        role, created = Role.objects.get_or_create(name="Super Administrador",  defaults={"description": "Este rol tiene todos los privilegios del sistema."})
        if created:
            self.stdout.write(self.style.SUCCESS('Rol "Super Administrador" creado.'))
        else:
            self.stdout.write(self.style.WARNING('El rol "Super Administrador" ya existe.'))

        # 3. Asigna TODOS los permisos al rol
        all_permissions = Permission.objects.all()
        role.permissions.set(all_permissions)
        self.stdout.write(self.style.SUCCESS(f'Se asignaron {all_permissions.count()} permisos al rol "Super Administrador".'))

        # 4. Crea el usuario Super Admin
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'El usuario con el email {email} ya existe. Saltando la creación.'))
            return

        user = User.objects.create_superuser(
            email=email,
            username=username,
            password=password,
            role=role,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'Superusuario "{user.email}" creado exitosamente.'))

        self.stdout.write(self.style.SUCCESS('Proceso de seeding finalizado.'))