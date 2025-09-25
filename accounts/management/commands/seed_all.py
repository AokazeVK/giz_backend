import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import Role, Permission
from dashboard.models import Departamento

# Estructura de árbol con TODOS los permisos de las vistas
TREE = {
    "label": "Permisos",
    "code": "permisos",
    "children": [
        {
            "label": "Usuarios",
            "code": "usuarios",
            "children": [
                {"label": "Crear Usuarios", "code": "crear_usuarios"},
                {"label": "Editar Usuarios", "code": "editar_usuarios"},
                {"label": "Eliminar Usuarios", "code": "eliminar_usuarios"},
                {"label": "Listar Usuarios", "code": "listar_usuarios"},
                {
                    "label": "Cambiar Contraseña Usuarios",
                    "code": "cambiar_contrasena_usuarios",
                },
                {"label": "Ver Usuario", "code": "ver_usuario"},
            ],
        },
        {
            "label": "Roles",
            "code": "roles",
            "children": [
                {"label": "Crear Roles", "code": "crear_roles"},
                {"label": "Editar Roles", "code": "editar_roles"},
                {"label": "Eliminar Roles", "code": "eliminar_roles"},
                {"label": "Listar Roles", "code": "listar_roles"},
                {"label": "Editar Permisos Rol", "code": "editar_permisos_roles"},
                {"label": "Ver Rol", "code": "ver_rol"},
            ],
        },
        {
            "label": "Auditoría",
            "code": "auditoria",
            "children": [
                {"label": "Ver Historial Global", "code": "ver_historial_global"},
            ],
        },
        {
            "label": "Difusión",
            "code": "difusion",
            "children": [
                {
                    "label": "Ministerios",
                    "code": "ministerios",
                    "children": [
                        {"label": "Crear Ministerios", "code": "crear_ministerios"},
                        {"label": "Editar Ministerios", "code": "editar_ministerios"},
                        {
                            "label": "Eliminar Ministerios",
                            "code": "eliminar_ministerios",
                        },
                        {"label": "Listar Ministerios", "code": "listar_ministerios"},
                        {"label": "Toggle Ministerio", "code": "toggle_estado"},
                    ],
                },
                {
                    "label": "Encargados",
                    "code": "encargados",
                    "children": [
                        {"label": "Crear Encargados", "code": "crear_encargados"},
                        {"label": "Editar Encargados", "code": "editar_encargados"},
                        {"label": "Eliminar Encargados", "code": "eliminar_encargados"},
                        {"label": "Listar Encargados", "code": "listar_encargados"},
                        {
                            "label": "Toggle Encargados",
                            "code": "toggle_estado_encargado",
                        },
                        {
                            "label": "Listar Encargados por Ministerio",
                            "code": "listar_encargados_por_ministerio",
                        },
                    ],
                },
                {
                    "label": "Convocatorias",
                    "code": "convocatorias",
                    "children": [
                        {"label": "Crear Convocatorias", "code": "crear_convocatorias"},
                        {
                            "label": "Editar Convocatorias",
                            "code": "editar_convocatorias",
                        },
                        {
                            "label": "Eliminar Convocatorias",
                            "code": "eliminar_convocatorias",
                        },
                        {
                            "label": "Listar Convocatorias",
                            "code": "listar_convocatorias",
                        },
                        {
                            "label": "Toggle Convocatoria",
                            "code": "toggle_estado_convocatoria",
                        },
                    ],
                },
                {
                    "label": "Fechas de Convocatoria",
                    "code": "fechas_convocatoria",
                    "children": [
                        {
                            "label": "Crear Fechas Convocatoria",
                            "code": "crear_fechas_convocatorias",
                        },
                        {
                            "label": "Editar Fechas Convocatoria",
                            "code": "editar_fechas_convocatorias",
                        },
                        {
                            "label": "Eliminar Fechas Convocatoria",
                            "code": "eliminar_fechas_convocatorias",
                        },
                        {
                            "label": "Listar Fechas Convocatoria",
                            "code": "listar_fechas_convocatorias",
                        },
                        {
                            "label": "Toggle Fecha Convocatoria",
                            "code": "toggle_estado_fecha_convocatoria",
                        },
                    ],
                },
                {
                    "label": "Archivos",
                    "code": "archivos",
                    "children": [
                        {
                            "label": "Crear Archivos",
                            "code": "crear_archivos_fechas_convocatorias",
                        },
                        {
                            "label": "Eliminar Archivos",
                            "code": "eliminar_archivos_fechas_convocatorias",
                        },
                        {
                            "label": "Listar Archivos",
                            "code": "listar_archivos_fechas_convocatorias",
                        },
                    ],
                },
                {
                    "label": "Departamentos",
                    "code": "departamentos",
                    "children": [
                        {"label": "Crear Departamentos", "code": "crear_departamentos"},
                        {"label": "Editar Departamentos", "code": "editar_departamentos"},
                        {"label": "Eliminar Departamentos", "code": "eliminar_departamentos"},
                        {"label": "Listar Departamentos", "code": "listar_departamentos"},
                    ],
                },
            ],
        },
        {
            "label": "Cursos",
            "code": "cursos",
            "children": [
                {"label": "Crear Cursos", "code": "crear_cursos"},
                {"label": "Editar Cursos", "code": "editar_cursos"},
                {"label": "Eliminar Cursos", "code": "eliminar_cursos"},
                {"label": "Listar Cursos", "code": "listar_cursos"},
                {"label": "Listar Cursos Activos", "code": "listar_cursos_activos"},
                {"label": "Toggle Curso", "code": "toggle_estado_curso"},
                {
                    "label": "Aumentar Visualizaciones",
                    "code": "aumentar_visualizaciones_curso",
                },
            ],
        },
        {
            "label": "Dashboard",
            "code": "dashboard",
            "children": [
                {"label": "Listar Dashboard", "code": "listar_dashboard"},
            ],
        },
        {
        "label": "Preparación",
        "code": "preparacion",
        "children": [
            {
                "label": "Empresas",
                "code": "empresas",
                "children": [
                    {"label": "Ver Empresas", "code": "ver_empresas"},
                    {"label": "Crear Empresas", "code": "crear_empresas"},
                    {"label": "Editar Empresas", "code": "editar_empresas"},
                    {"label": "Eliminar Empresas", "code": "eliminar_empresas"},
                ],
            },
            {
                "label": "Asesoramientos",
                "code": "asesoramientos",
                "children": [
                    {"label": "Ver Asesoramientos", "code": "ver_asesoramientos"},
                    {"label": "Crear Asesoramientos", "code": "crear_asesoramientos"},
                    {"label": "Editar Asesoramientos", "code": "editar_asesoramientos"},
                    {"label": "Eliminar Asesoramientos", "code": "eliminar_asesoramientos"},
                    {"label": "Ver Asesoramientos Públicos", "code": "ver_asesoramientos_publicos"},
                    {"label": "Listar Encargados Asesoramiento", "code": "listar_encargados_asesoramiento"},
                    {"label": "Listar Archivos Asesoramiento", "code": "listar_archivos_asesoramiento"},
                ],
            },
            {
                "label": "Solicitudes de Asesoramiento",
                "code": "solicitudes_asesoramiento",
                "children": [
                    {"label": "Ver Solicitudes", "code": "ver_solicitudes_asesoramiento"},
                    {"label": "Crear Solicitudes", "code": "crear_solicitudes_asesoramiento"},
                    {"label": "Aprobar Solicitudes", "code": "aprobar_solicitudes_asesoramiento"},
                    {"label": "Rechazar Solicitudes", "code": "rechazar_solicitudes_asesoramiento"},
                    {"label": "Completar Solicitudes", "code": "completar_solicitudes_asesoramiento"},
                    {"label": "Cancelar Solicitudes", "code": "cancelar_solicitudes_asesoramiento"},
                ],
            },
            {
                "label": "Publicaciones Comunidad de Empresa",
                "code": "publicaciones_comunidad",
                "children": [
                    {"label": "Ver Publicaciones", "code": "ver_publicaciones_comunidad"},
                    {"label": "Crear Publicaciones", "code": "crear_publicaciones_comunidad"},
                    {"label": "Editar Publicaciones", "code": "editar_publicaciones_comunidad"},
                    {"label": "Eliminar Publicaciones", "code": "eliminar_publicaciones_comunidad"},
                ],
            },
            {
                "label": "Archivos de Asesoramiento",
                "code": "archivos_asesoramiento",
                "children": [
                    {"label": "Listar Archivos", "code": "listar_archivos_asesoramiento"},
                    {"label": "Crear Archivos", "code": "crear_archivos_asesoramiento"},
                    {"label": "Eliminar Archivos", "code": "eliminar_archivos_asesoramiento"},
                ],
            },
            {
                "label": "Encargados de Asesoramiento",
                "code": "encargados_asesoramiento",
                "children": [
                    {"label": "Listar Encargados", "code": "listar_encargados_asesoramiento"},
                    {"label": "Crear Encargados", "code": "crear_encargados_asesoramiento"},
                    {"label": "Editar Encargados", "code": "editar_encargados_asesoramiento"},
                    {"label": "Eliminar Encargados", "code": "eliminar_encargados_asesoramiento"},
                ],
            },
        ],
    },
        {
            "label": "Sello",
            "code": "sello",
            "children": [
                {
                    "label": "Tipos de Sello",
                    "code": "tipos_sello",
                    "children": [
                        {
                            "label": "Listar Tipos de Sello",
                            "code": "listar_tipos_sello",
                        },
                        {"label": "Crear Tipos de Sello", "code": "crear_tipos_sello"},
                        {
                            "label": "Editar Tipos de Sello",
                            "code": "editar_tipos_sello",
                        },
                        {
                            "label": "Eliminar Tipos de Sello",
                            "code": "eliminar_tipos_sello",
                        },
                    ],
                },
                {
                    "label": "Requisitos",
                    "code": "requisitos",
                    "children": [
                        {"label": "Listar Requisitos", "code": "listar_requisitos"},
                        {"label": "Crear Requisitos", "code": "crear_requisitos"},
                        {"label": "Editar Requisitos", "code": "editar_requisitos"},
                        {"label": "Eliminar Requisitos", "code": "eliminar_requisitos"},
                    ],
                },
                {
                    "label": "Requisito Input",
                    "code": "requisito_input",
                    "children": [
                        {
                            "label": "Listar Requisito Input",
                            "code": "listar_requisitos_input",
                        },
                        {
                            "label": "Crear Requisito Input",
                            "code": "crear_requisitos_input",
                        },
                        {
                            "label": "Editar Requisito Input",
                            "code": "editar_requisitos_input",
                        },
                        {
                            "label": "Eliminar Requisito Input",
                            "code": "eliminar_requisitos_input",
                        },
                        {
                            "label": "Alternar Requisito Input",
                            "code": "editar_requisitos_input",
                        },
                        {
                            "label": "Listar Requisitos Postulacion",
                            "code": "listar_requisitos_postulacion",
                        },
                    ],
                },
                {
                    "label": "Requisito Input Valor",
                    "code": "requisito_input_valor",
                    "children": [
                        {"label": "Ver Requisitos Input Valor", "code": "ver_requisitos_input_valor"},
                        {"label": "Crear Requisitos Input Valor", "code": "crear_requisitos_input_valor"},
                        {"label": "Editar Requisitos Input Valor", "code": "editar_requisitos_input_valor"},
                        {"label": "Eliminar Requisitos Input Valor", "code": "eliminar_requisitos_input_valor"},
                    ],
                },
                # Aquí se añadieron los nuevos permisos para Evaluacion Dato
                {
                    "label": "Evaluacion Dato",
                    "code": "evaluacion_dato",
                    "children": [
                        {"label": "Listar Evaluacion Dato", "code": "listar_evaluacion_dato"},
                        {"label": "Crear Evaluacion Dato", "code": "crear_evaluacion_dato"},
                        {"label": "Editar Evaluacion Dato", "code": "editar_evaluacion_dato"},
                        {"label": "Eliminar Evaluacion Dato", "code": "eliminar_evaluacion_dato"},
                    ],
                },
                {
                    "label": "Checklist de Evaluación",
                    "code": "checklist",
                    "children": [
                        {
                            "label": "Listar Checklist",
                            "code": "listar_checklist_evaluacion",
                        },
                        {
                            "label": "Crear Checklist",
                            "code": "crear_checklist_evaluacion",
                        },
                        {
                            "label": "Editar Checklist",
                            "code": "editar_checklist_evaluacion",
                        },
                        {
                            "label": "Eliminar Checklist",
                            "code": "eliminar_checklist_evaluacion",
                        },
                        {
                            "label": "Alternar Checklist",
                            "code": "editar_checklist_evaluacion",
                        },
                    ],
                },
                {
                    "label": "Evaluaciones",
                    "code": "evaluaciones",
                    "children": [
                        {"label": "Listar Evaluaciones", "code": "listar_evaluaciones"},
                        {"label": "Crear Evaluaciones", "code": "crear_evaluaciones"},
                        {"label": "Editar Evaluaciones", "code": "editar_evaluaciones"},
                        {
                            "label": "Eliminar Evaluaciones",
                            "code": "eliminar_evaluaciones",
                        },
                        {
                            "label": "Cambiar Estado de Evaluación",
                            "code": "editar_evaluaciones",
                        },
                    ],
                },
                {
                    "label": "Fases de Evaluación",
                    "code": "fases_evaluacion",
                    "children": [
                        {
                            "label": "Listar Fases de Evaluación",
                            "code": "listar_fases_evaluacion",
                        },
                        {
                            "label": "Crear Fases de Evaluación",
                            "code": "crear_fases_evaluacion",
                        },
                        {
                            "label": "Editar Fases de Evaluación",
                            "code": "editar_fases_evaluacion",
                        },
                        {
                            "label": "Eliminar Fases de Evaluación",
                            "code": "eliminar_fases_evaluacion",
                        },
                        {
                            "label": "Alternar Fases de Evaluación",
                            "code": "editar_fases_evaluacion",
                        },
                    ],
                },
                {
                    "label": "Enlaces",
                    "code": "enlaces",
                    "children": [
                        {"label": "Ver Enlaces", "code": "ver_enlaces"},
                        {"label": "Crear Enlaces", "code": "crear_enlaces"},
                        {"label": "Editar Enlaces", "code": "editar_enlaces"},
                        {"label": "Eliminar Enlaces", "code": "eliminar_enlaces"},
                        {"label": "Ver Enlaces Públicos", "code": "ver_enlaces_publicos"},
                    ],
                },
            ],
        },
        # NUEVA SECCIÓN DE RECONOCIMIENTO
        {
            "label": "Reconocimiento",
            "code": "reconocimiento",
            "children": [
                {
                    "label": "Eventos",
                    "code": "eventos",
                    "children": [
                        {"label": "Listar Eventos", "code": "listar_eventos"},
                        {"label": "Crear Eventos", "code": "crear_eventos"},
                        {"label": "Editar Eventos", "code": "editar_eventos"},
                        {"label": "Eliminar Eventos", "code": "eliminar_eventos"},
                    ],
                }
            ],
        },
        {
            "label": "Comunidad",
            "code": "comunidad",
            "children": [
                {"label": "Listar comunidad", "code": "listar_comunidad"},
            ],
        },
    ],
}


def upsert_permissions(node, parent=None):
    """
    Función recursiva para crear o actualizar los permisos
    basándose en la estructura de árbol definida.
    """
    obj, _ = Permission.objects.get_or_create(
        code=node["code"], defaults={"label": node["label"], "parent": parent}
    )
    if obj.label != node["label"] or obj.parent_id != (parent.id if parent else None):
        obj.label = node["label"]
        obj.parent = parent
        obj.save()
    for child in node.get("children", []):
        upsert_permissions(child, obj)


class Command(BaseCommand):
    help = "Crea/actualiza los permisos, el rol de Super Admin, un superusuario y los departamentos."

    @transaction.atomic
    def handle(self, *args, **options):
        # Datos para el superusuario
        email = "admin@mail.com"
        password = "Hola1234"
        username = "superadmin"

        # Nombres de los departamentos a crear
        departamentos_bolivia = [
            "Beni",
            "Chuquisaca",
            "Cochabamba",
            "La Paz",
            "Oruro",
            "Pando",
            "Potosí",
            "Santa Cruz",
            "Tarija",
        ]

        self.stdout.write(self.style.NOTICE("Iniciando el proceso de seeding..."))

        # 1. Crea/actualiza todos los permisos
        upsert_permissions(TREE, None)
        self.stdout.write(
            self.style.SUCCESS("Permisos base creados/actualizados exitosamente.")
        )

        # 2. Crea o obtiene el rol de Super Administrador
        role, created = Role.objects.get_or_create(
            name="Super Administrador",
            defaults={
                "description": "Este rol tiene todos los privilegios del sistema."
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Rol "Super Administrador" creado.'))
        else:
            self.stdout.write(
                self.style.WARNING('El rol "Super Administrador" ya existe.')
            )

        # 3. Asigna TODOS los permisos al rol
        all_permissions = Permission.objects.all()
        role.permissions.set(all_permissions)
        self.stdout.write(
            self.style.SUCCESS(
                f'Se asignaron {all_permissions.count()} permisos al rol "Super Administrador".'
            )
        )

        # 4. Crea los departamentos
        self.stdout.write(self.style.NOTICE("Creando los departamentos..."))
        for depto_name in departamentos_bolivia:
            depto, created = Departamento.objects.get_or_create(nombre=depto_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Departamento "{depto.nombre}" creado.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'El departamento "{depto.nombre}" ya existe. Saltando.'
                    )
                )
        self.stdout.write(
            self.style.SUCCESS("Departamentos creados/actualizados exitosamente.")
        )

        # 5. Crea el usuario Super Admin
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"El usuario con el email {email} ya existe. Saltando la creación."
                )
            )
            return

        user = User.objects.create_superuser(
            email=email, username=username, password=password, role=role, is_active=True
        )
        self.stdout.write(
            self.style.SUCCESS(f'Superusuario "{user.email}" creado exitosamente.')
        )

        self.stdout.write(self.style.SUCCESS("Proceso de seeding finalizado."))