from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from preparacion.models import Empresa
from accounts.serializers import UserSerializer
from accounts.models import User
# Importa los nuevos modelos y serializadores
from .models import (
    Enlaces,
    RequisitoInputValor,
    TipoSello,
    Requisito,
    RequisitoInput,
    ChecklistEvaluacion,
    Evaluacion,
    EvaluacionFases,
    EvaluacionDato
)
from .serializers import (
    EnlacesSerializer,
    RequisitoInputValorSerializer,
    TipoSelloSerializer,
    RequisitoSerializer,
    RequisitoInputSerializer,
    ChecklistEvaluacionSerializer,
    EvaluacionSerializer,
    EvaluacionFasesSerializer,
    TipoSelloSerializerWithoutAllRelations,
    EvaluacionDatoSerializer
)
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action

# Importación de la tarea de Celery
from .task import enviar_evaluacion_email


class TipoSelloViewSet(viewsets.ModelViewSet):
    queryset = TipoSello.objects.all()
    serializer_class = TipoSelloSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_tipos_sello",
        "retrieve": "listar_tipos_sello",
        "create": "crear_tipos_sello",
        "update": "editar_tipos_sello",
        "partial_update": "editar_tipos_sello",
        "destroy": "eliminar_tipos_sello",
    }

    def get_queryset(self):
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            evaluaciones_qs = Evaluacion.objects.filter(
                gestion=gestion
            ).prefetch_related("evaluadores")
            return TipoSello.objects.all().prefetch_related(
                "requisitos__inputs", Prefetch("evaluaciones", queryset=evaluaciones_qs)
            )
        return TipoSello.objects.all().prefetch_related(
            "requisitos__inputs", "evaluaciones__evaluadores"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["gestion"] = self.request.COOKIES.get("gestion")
        return context

    def perform_create(self, serializer):
        tiposello = serializer.save()
        log_user_action(
            self.request.user, f"Creó Tipo de Sello: {tiposello.nombre}", self.request
        )

    def perform_update(self, serializer):
        tiposello = serializer.save()
        log_user_action(
            self.request.user,
            f"Actualizó Tipo de Sello: {tiposello.nombre}",
            self.request,
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, f"Eliminó Tipo de Sello: {instance.nombre}", self.request
        )
        super().perform_destroy(instance)


class RequisitoViewSet(viewsets.ModelViewSet):
    queryset = Requisito.objects.all().prefetch_related("inputs")
    serializer_class = RequisitoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_requisitos",
        "retrieve": "listar_requisitos",
        "create": "crear_requisitos",
        "update": "editar_requisitos",
        "partial_update": "editar_requisitos",
        "destroy": "eliminar_requisitos",
        "listar_tipos_sello": "listar_requisitos",
    }

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            qs = qs.filter(gestion=gestion)
        return qs

    def perform_create(self, serializer):
        gestion = self.request.COOKIES.get("gestion")
        if not gestion:
            return Response(
                {"error": "La cookie 'gestion' es requerida para crear un requisito."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        requisito = serializer.save(gestion=gestion)
        log_user_action(
            self.request.user, f"Creó un Requisito con ID: {requisito.id}", self.request
        )

    def perform_update(self, serializer):
        requisito = serializer.save()
        log_user_action(
            self.request.user,
            f"Actualizó un Requisito con ID: {requisito.id}",
            self.request,
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, f"Eliminó Requisito con ID: {instance.id}", self.request
        )
        super().perform_destroy(instance)

    @action(detail=False, methods=["get"], url_path="tipos-sello")
    def listar_tipos_sello(self, request):
        """
        Listar todos los tipos de sello disponibles.
        """
        tipos_sello = (
            TipoSello.objects.all()
        )  #  Busca todos los objetos del modelo TipoSello
        from .serializers import TipoSelloSerializer

        serializer = TipoSelloSerializer(tipos_sello, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RequisitoInputViewSet(viewsets.ModelViewSet):
    queryset = RequisitoInput.objects.all()
    serializer_class = RequisitoInputSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_requisitos_input",
        "retrieve": "listar_requisitos_input",
        "create": "crear_requisitos_input",
        "update": "editar_requisitos_input",
        "partial_update": "editar_requisitos_input",
        "destroy": "eliminar_requisitos_input",
        "toggle_status": "editar_requisitos_input",
        "get_requisitos_postulacion": "listar_requisitos_postulacion",
        "get_tipos_sellos": "listar_requisitos_postulacion",
    }

    @action(
        detail=False,
        methods=["get"],
        url_path="requisitos_postulacion/(?P<tipoSello_id>[^/.]+)",
    )
    def get_requisitos_postulacion(self, request, tipoSello_id=None):
        """
        Devuelve los RequisitoInput del primer Requisito que pertenezca a un TipoSello específico y a la gestión actual.
        """
        gestion = request.COOKIES.get("gestion")

        if not gestion:
            return Response(
                {"error": "La cookie 'gestion' es requerida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filtra por el tipo de sello y la gestión, luego toma el primero
        requisito_encontrado = Requisito.objects.filter(
            tipoSello__id=tipoSello_id, gestion=gestion
        ).first()

        if not requisito_encontrado:
            return Response(
                {
                    "message": "No se encontró ningún requisito para el tipo de sello y gestión especificados."
                },
                status=status.HTTP_200_OK,
            )

        # Filtra los RequisitoInput que pertenecen al requisito encontrado
        requisitos_input = RequisitoInput.objects.filter(requisito=requisito_encontrado)

        serializer = self.get_serializer(requisitos_input, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="tipos_sellos")
    def get_tipos_sellos(self, request):
        tipo_sello = TipoSello.objects.filter(is_active=True).order_by("id")
        serializer = TipoSelloSerializerWithoutAllRelations(tipo_sello, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        input_instance = serializer.save()
        log_user_action(
            self.request.user,
            f"Creó RequisitoInput: {input_instance.label}",
            self.request,
        )

    def perform_update(self, serializer):
        input_instance = serializer.save()
        log_user_action(
            self.request.user,
            f"Actualizó RequisitoInput: {input_instance.label}",
            self.request,
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, f"Eliminó RequisitoInput: {instance.label}", self.request
        )
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        """
        Alterna el estado (activo/inactivo) de un RequisitoInput.
        """
        requisito_input = self.get_object()
        requisito_input.is_active = not requisito_input.is_active
        requisito_input.save()
        log_user_action(
            self.request.user,
            f"Se alternó el estado de RequisitoInput con ID: {requisito_input.id} a {requisito_input.is_active}",
            self.request,
        )
        return Response(
            {
                "message": f"El estado del RequisitoInput ha sido cambiado a {requisito_input.is_active}."
            },
            status=status.HTTP_200_OK,
        )


class ChecklistEvaluacionViewSet(viewsets.ModelViewSet):
    # El serializador ya maneja la relación
    queryset = ChecklistEvaluacion.objects.all()
    serializer_class = ChecklistEvaluacionSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_checklist_evaluacion",
        "retrieve": "listar_checklist_evaluacion",
        "create": "crear_checklist_evaluacion",
        "update": "editar_checklist_evaluacion",
        "partial_update": "editar_checklist_evaluacion",
        "destroy": "eliminar_checklist_evaluacion",
        "toggle_status": "editar_checklist_evaluacion",
    }

    def perform_create(self, serializer):
        checklist = serializer.save()
        log_user_action(
            self.request.user,
            f"Creó Checklist de Evaluación: {checklist.nombre}",
            self.request,
        )

    def perform_update(self, serializer):
        checklist = serializer.save()
        log_user_action(
            self.request.user,
            f"Actualizó Checklist de Evaluación: {checklist.nombre}",
            self.request,
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user,
            f"Eliminó Checklist de Evaluación: {instance.nombre}",
            self.request,
        )
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        """
        Alterna el estado (activo/inactivo) de un Checklist de Evaluación.
        """
        checklist = self.get_object()
        checklist.is_active = not checklist.is_active
        checklist.save()
        log_user_action(
            self.request.user,
            f"Se alternó el estado de Checklist con ID: {checklist.id} a {checklist.is_active}",
            self.request,
        )
        return Response(
            {
                "message": f"El estado del Checklist ha sido cambiado a {checklist.is_active}."
            },
            status=status.HTTP_200_OK,
        )


# Nuevo ViewSet para las fases de evaluación
class EvaluacionFasesViewSet(viewsets.ModelViewSet):
    queryset = EvaluacionFases.objects.all().prefetch_related("checklists")
    serializer_class = EvaluacionFasesSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_fases_evaluacion",
        "retrieve": "listar_fases_evaluacion",
        "create": "crear_fases_evaluacion",
        "update": "editar_fases_evaluacion",
        "partial_update": "editar_fases_evaluacion",
        "destroy": "eliminar_fases_evaluacion",
        "toggle_status": "editar_fases_evaluacion",
    }

    def perform_create(self, serializer):
        # Obtiene el ID de la evaluación del validated_data
        evaluacion_id = serializer.validated_data.get("evaluacion").id

        # Filtra la evaluación para obtener el campo 'gestion'
        try:
            evaluacion = Evaluacion.objects.get(id=evaluacion_id)
            gestion = evaluacion.gestion
        except Evaluacion.DoesNotExist:
            return Response(
                {"error": "La evaluación proporcionada no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Asigna la gestión a la instancia de la fase antes de guardar
        fase = serializer.save(gestion=gestion)
        log_user_action(
            self.request.user, f"Creó una fase: {fase.nombre}", self.request
        )

    def perform_update(self, serializer):
        fase = serializer.save()
        log_user_action(
            self.request.user, f"Actualizó la fase: {fase.nombre}", self.request
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, f"Eliminó la fase: {instance.nombre}", self.request
        )
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        """
        Alterna el estado (activo/inactivo) de una fase de evaluación.
        """
        fase = self.get_object()
        fase.is_active = not fase.is_active
        fase.save()
        log_user_action(
            self.request.user,
            f"Se alternó el estado de la fase con ID: {fase.id} a {fase.is_active}",
            self.request,
        )
        return Response(
            {"message": f"El estado de la fase ha sido cambiado a {fase.is_active}."},
            status=status.HTTP_200_OK,
        )


class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.all().prefetch_related(
        "evaluadores", "fases__checklists"
    )
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_evaluaciones",
        "retrieve": "listar_evaluaciones",
        "create": "crear_evaluaciones",
        "update": "editar_evaluaciones",
        "partial_update": "editar_evaluaciones",
        "destroy": "eliminar_evaluaciones",
        "cambiar_estado": "editar_evaluaciones",
        "listar_tipos_sello": "listar_evaluaciones",
        "listar_evaluadores": "listar_evaluaciones",
    }

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            # Aquí se filtra por la gestión de la evaluación, no de las fases
            qs = qs.filter(gestion=gestion)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["gestion"] = self.request.COOKIES.get("gestion")
        return context

    def perform_create(self, serializer):
        evaluacion = serializer.save()
        log_user_action(
            self.request.user,
            f"Creó Evaluación para: {evaluacion.tipoSello.nombre} en gestión {evaluacion.gestion}",
            self.request,
        )

        # Llama a la tarea de Celery de forma asíncrona
        evaluadores_ids = list(evaluacion.evaluadores.values_list("id", flat=True))
        if evaluadores_ids:
            enviar_evaluacion_email.delay(evaluacion.id, evaluadores_ids)

    def perform_update(self, serializer):
        old_evaluadores = set(self.get_object().evaluadores.all())
        evaluacion = serializer.save()
        new_evaluadores = set(evaluacion.evaluadores.all())
        added_evaluadores = new_evaluadores - old_evaluadores

        log_user_action(
            self.request.user,
            f"Actualizó Evaluación para: {evaluacion.tipoSello.nombre} en gestión {evaluacion.gestion}",
            self.request,
        )

        if added_evaluadores:
            added_evaluadores_ids = list(user.id for user in added_evaluadores)
            enviar_evaluacion_email.delay(evaluacion.id, added_evaluadores_ids)
            log_user_action(
                self.request.user,
                f"Se programó el envío de correo a {len(added_evaluadores)} nuevos evaluadores.",
                self.request,
            )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user,
            f"Eliminó Evaluación para: {instance.tipoSello.nombre} en gestión {instance.gestion}",
            self.request,
        )
        super().perform_destroy(instance)

    @action(detail=False, methods=["get"], url_path="evaluadores")
    def listar_evaluadores(self, request):
        """
        Lista todos los usuarios con rol 'Evaluador'.
        Se controla con el permiso 'listar_evaluaciones' (o 'listar_evaluaciones').
        """
        evaluadores = User.objects.filter(role__name="Evaluador", is_active=True)

        serializer = UserSerializer(evaluadores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="tipos-sello")
    def listar_tipos_sello(self, request):
        """
        Lista todos los TipoSello con sus requisitos e inputs.
        Usa el permiso listar_evaluaciones.
        """
        gestion = request.COOKIES.get("gestion")
        if gestion:
            evaluaciones_qs = Evaluacion.objects.filter(
                gestion=gestion
            ).prefetch_related("evaluadores")
            tipos_sello = TipoSello.objects.all().prefetch_related(
                "requisitos__inputs", Prefetch("evaluaciones", queryset=evaluaciones_qs)
            )
        else:
            tipos_sello = TipoSello.objects.all().prefetch_related(
                "requisitos__inputs", "evaluaciones__evaluadores"
            )

        serializer = TipoSelloSerializer(
            tipos_sello, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        evaluacion = self.get_object()
        new_status = request.data.get("estado")

        if new_status and new_status in dict(Evaluacion.ESTADO_CHOICES):
            evaluacion.estado = new_status
            evaluacion.save()
            log_user_action(
                self.request.user,
                f"Cambió el estado de la evaluación {evaluacion.id} a '{new_status}'",
                self.request,
            )
            return Response(
                {"message": f"Estado de la evaluación cambiado a '{new_status}'."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Estado inválido proporcionado."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RequisitoInputValorViewSet(viewsets.ModelViewSet):
    serializer_class = RequisitoInputValorSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap] # 👈 Aplica los permisos

    permission_code_map = { # 👈 Define el mapa de permisos
        "list": "ver_requisitos_input_valor",
        "retrieve": "ver_requisitos_input_valor",
        "create": "crear_requisitos_input_valor",
        "update": "editar_requisitos_input_valor",
        "partial_update": "editar_requisitos_input_valor",
        "destroy": "eliminar_requisitos_input_valor",
        "get_postulacion_usuario": "ver_requisitos_input_valor",
        "get_evaluacion_datos": "ver_requisitos_input_valor",
    }
    
    def get_queryset(self):
        """
        Sobrescribe el queryset para mostrar la postulación de la empresa
        en lugar de la de un usuario individual.
        """
        user = self.request.user
        gestion = self.request.COOKIES.get("gestion")
        
        # Validar si el usuario tiene una empresa y si la gestión está presente
        if not hasattr(user, 'empresa') or not user.empresa or not gestion:
            return RequisitoInputValor.objects.none()

        # Filtrar por la empresa del usuario y la gestión actual
        qs = RequisitoInputValor.objects.filter(
            empresa=user.empresa,
            gestion=gestion,
        )
        return qs

    def create(self, request, *args, **kwargs):
        """
        Maneja la lógica de validación para evitar duplicados por empresa.
        """
        user = self.request.user
        gestion = self.request.COOKIES.get('gestion')
        
        # 1. Verificar si el usuario está asociado a una empresa
        if not hasattr(user, 'empresa') or not user.empresa:
            return Response({"detail": "El usuario no está vinculado a una empresa."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_empresa = user.empresa
        
        # 2. Obtener el requisito_input desde los datos de la petición
        requisito_input_id = request.data.get('requisito_input')
        if not requisito_input_id:
            return Response({"detail": "El campo 'requisito_input' es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Validar si ya existe una postulación para la empresa
        if RequisitoInputValor.objects.filter(
            empresa=user_empresa, 
            requisito_input_id=requisito_input_id, 
            gestion=gestion
        ).exists():
            return Response(
                {"detail": "Su empresa ya ha enviado este requisito para esta gestión."}, 
                status=status.HTTP_409_CONFLICT
            )

        # 4. Si no existe, proceder con la creación
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """
        Asigna el usuario, empresa y gestión antes de guardar el objeto.
        """
        user = self.request.user
        gestion = self.request.COOKIES.get('gestion')
        user_empresa = user.empresa

        serializer.save(
            usuario=user,
            empresa=user_empresa,
            gestion=gestion
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="postulacion_usuario/(?P<tipoSello_id>[^/.]+)",
    )
    def get_postulacion_usuario(self, request, tipoSello_id=None):
        """
        Retorna los valores de los requisitos de una empresa para un tipo de sello y gestión específicos.
        """
        user = request.user
        gestion = self.request.COOKIES.get("gestion")

        if not hasattr(user, 'empresa') or not user.empresa:
            return Response({"detail": "El usuario no está vinculado a una empresa."}, status=status.HTTP_400_BAD_REQUEST)

        qs = RequisitoInputValor.objects.filter(
            empresa=user.empresa, # <--- Cambio clave para filtrar por empresa
            requisito_input__requisito__tipoSello__id=tipoSello_id,
            gestion=gestion,
        )

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="evaluacion",
    )
    def get_evaluacion_datos(self, request):
        """
        Retorna los datos de los Requisitos de usuarios agrupados por requisito.
        Solo accesible si el usuario logueado es evaluador de ese tipoSello y gestión.
        """
        gestion = self.request.COOKIES.get("gestion")
        # 1. Verificar si el usuario actual es un evaluador asignado a la evaluación.
        evaluacion_exists = Evaluacion.objects.filter(
            gestion=gestion,
            evaluadores=request.user,
        ).exists()

        print(gestion)

        if not evaluacion_exists:
            return Response(
                {"detail": "No tienes permiso para ver esta información."}, status=403
            )

        evaluador = User.objects.get(
            role__name='Evaluador',
            id=request.user.id
        )


        evaluaciones = Evaluacion.objects.filter(
            evaluadores__in=[evaluador]


        )

        # 2. Obtener los usuarios que han enviado datos para este tipoSello y gestión.
        qs = RequisitoInputValor.objects.filter(

            gestion=gestion,
            requisito_input__requisito__tipoSello__evaluaciones__in=evaluaciones,
        ).select_related(
            "usuario","requisito_input", "requisito_input__requisito",
        )

        # 3. Agrupar los datos para la respuesta.

        grouped_data = {}
        for item in qs:
            requisito_id = item.requisito_input.requisito.id
            requisito_nombre = item.requisito_input.requisito.nombre
            tipo_sello = item.requisito_input.requisito.tipoSello.nombre
            tipo_sello_id = item.requisito_input.requisito.tipoSello.id
            usuario_id = item.usuario.id
            usuario_email = item.usuario.email
            empresa = item.usuario.empresa.nombre
            empresa_id = item.usuario.empresa.id

            # Crear la estructura si no existe
            if requisito_id not in grouped_data:
                grouped_data[requisito_id] = {
                    "requisito_id": requisito_id,
                    "requisito_nombre": requisito_nombre,
                    
                    "usuarios_con_datos": {},
                }

            if usuario_id not in grouped_data[requisito_id]["usuarios_con_datos"]:

                grouped_data[requisito_id]["usuarios_con_datos"][usuario_id] = {
                    "usuario_id": usuario_id,
                    "usuario_email": usuario_email,
                    "tipo_sello":tipo_sello,
                    "tipo_sello_id":tipo_sello_id,
                    "empresa":empresa,
                    "empresa_id":empresa_id,
                    "valores_requisito": [],

                }

            # Serializar el valor y agregarlo
            serializer = self.get_serializer(item)
            grouped_data[requisito_id]["usuarios_con_datos"][usuario_id][
                "valores_requisito"
            ].append(serializer.data)

        # 4. Convertir a una lista de diccionarios para la respuesta final.
        response_data = []
        for requisito_id, data in grouped_data.items():
            data["usuarios_con_datos"] = list(data["usuarios_con_datos"].values())
            response_data.append(data)

        return Response(response_data)
    
    @action(
        detail=False,
        methods=["get"],
        url_path="fases-evaluacion/(?P<tipoSello_id>[^/.]+)",
    )
    def get_fases_evaluacion(self, request, tipoSello_id=None):
        """
        Retorna las fases de evaluación con sus checklists asignados para el evaluador actual.
        Filtra por la gestión de la cookie.
        """
        gestion = self.request.COOKIES.get("gestion")

        if not gestion:
            return Response({"detail": "La gestión es requerida."}, status=400)

        # 1. Obtener las evaluaciones a las que el usuario actual está asignado en la gestión actual.
        evaluaciones_del_evaluador = Evaluacion.objects.filter(
            evaluadores=request.user, gestion=gestion, tipoSello_id=tipoSello_id
        )

        # 2. Filtrar las fases que pertenecen a esas evaluaciones y a la gestión actual.
        fases_qs = EvaluacionFases.objects.filter(
            evaluacion__in=evaluaciones_del_evaluador, gestion=gestion
        ).prefetch_related(
            # Optimiza la consulta precargando los checklists para cada fase.
            Prefetch(
                "checklists",
                queryset=ChecklistEvaluacion.objects.all(),
                to_attr="related_checklists",
            )
        )

        # 3. Serializar y devolver la respuesta.
        serializer = EvaluacionFasesSerializer(fases_qs, many=True)
        return Response(serializer.data)

class EvaluacionDatoViewSet(viewsets.ModelViewSet):
    queryset = EvaluacionDato.objects.all()
    serializer_class = EvaluacionDatoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_evaluacion_dato",
        "retrieve": "listar_evaluacion_dato",
        "create": "crear_evaluacion_dato",
        "update": "editar_evaluacion_dato",
        "partial_update": "editar_evaluacion_dato",
        "destroy": "eliminar_evaluacion_dato",
    }

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            qs = qs.filter(gestion=gestion, usuario=self.request.user)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["gestion"] = self.request.COOKIES.get("gestion")
        return context
    
    def perform_create(self, serializer):
        # El serializador ya maneja la lógica de la gestión y FaseEmpresa
        dato = serializer.save(usuario=self.request.user)
        log_user_action(
            self.request.user, 
            f"Creó un registro de evaluación de dato con puntaje: {dato.puntaje} para el checklist ID: {dato.checklist_evaluacion.id}", 
            self.request
        )

    def perform_update(self, serializer):
        # El serializador ya maneja la lógica de la gestión y FaseEmpresa
        dato = serializer.save()
        log_user_action(
            self.request.user, 
            f"Actualizó un registro de evaluación de dato con puntaje: {dato.puntaje} para el checklist ID: {dato.checklist_evaluacion.id}", 
            self.request
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, 
            f"Eliminó un registro de evaluación de dato con puntaje: {instance.puntaje} para el checklist ID: {instance.checklist_evaluacion.id}", 
            self.request
        )
        super().perform_destroy(instance)
    
    @action(detail=False, methods=['get'], url_path='por-evaluador')
    def get_by_evaluador(self, request):
        gestion = self.request.COOKIES.get("gestion")
        usuario_evaluador = request.query_params.get('usuario_evaluador_id')
        checklist_id = request.query_params.get('checklist_id')

        if not all([gestion, usuario_evaluador, checklist_id]):
            return Response({"error": "Parámetros 'gestion', 'usuario_evaluador_id' y 'checklist_id' son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Filtra por usuario_evaluador_id y checklist_id y gestion
            queryset = EvaluacionDato.objects.filter(
                usuario=usuario_evaluador,
                checklist_evaluacion=checklist_id,
                gestion=gestion
            ).select_related('empresa', 'checklist_evaluacion')
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='por-empresa')
    def get_by_empresa(self, request):
        gestion = self.request.COOKIES.get("gestion")
        empresa_id = request.query_params.get('empresa_id')
        checklist_id = request.query_params.get('checklist_id')
        
        if not all([gestion, empresa_id, checklist_id]):
            return Response({"error": "Parámetros 'gestion', 'empresa_id' y 'checklist_id' son requeridos."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Filtra por empresa_id y checklist_id y gestion
            queryset = EvaluacionDato.objects.filter(
                empresa=empresa_id,
                checklist_evaluacion=checklist_id,
                gestion=gestion
            ).select_related('usuario', 'checklist_evaluacion')
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'], url_path='agrupados-por-fase')
    def evaluaciones_agrupadas(self, request):
        """
        Retorna los registros de EvaluacionDato agrupados por fase de evaluación.
        """
        gestion = self.request.COOKIES.get('gestion')
        empresa_id = request.query_params.get('empresa_id')
        checklist_id = request.query_params.get('checklist_id')
        usuario_id = request.query_params.get('usuario_id')
        
        if not all([gestion, empresa_id, checklist_id, usuario_id]):
            return Response(
                {"error": "Los parámetros 'empresa_id', 'checklist_id' y 'usuario_id' son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Obtener los datos de evaluación con las relaciones necesarias
            queryset = EvaluacionDato.objects.filter(
                empresa__id=empresa_id,
                checklist_evaluacion__id=checklist_id,
                usuario__id=usuario_id,
                gestion=gestion
            ).select_related(
                'usuario', 
                'empresa', 
                'checklist_evaluacion__evaluacion_fase',
            )

            # Agrupar los datos por fase
            fases_agrupadas = {}
            for dato in queryset:
                fase = dato.checklist_evaluacion.evaluacion_fase
                if fase.nombre not in fases_agrupadas:
                    fases_agrupadas[fase.nombre] = {
                        "id_fase": fase.id,
                        "nombre_fase": fase.nombre,
                        "evaluaciones": []
                    }
                
                # Serializar el dato para un formato de respuesta detallado
                evaluacion_data = {
                    "id_evaluacion_dato": dato.id,
                    "puntaje": dato.puntaje,
                    "comentarios": dato.comentarios,
                    "nombre_empresa": dato.empresa.nombre,
                    "usuario_calificador": dato.usuario.email,
                    "checklist": {
                        "id": dato.checklist_evaluacion.id,
                        "nombre": dato.checklist_evaluacion.nombre,
                        "porcentaje_maximo": dato.checklist_evaluacion.porcentaje
                    }
                }
                fases_agrupadas[fase.nombre]["evaluaciones"].append(evaluacion_data)
            
            # Convertir el diccionario a una lista para la respuesta final
            response_data = list(fases_agrupadas.values())
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Ocurrió un error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @action(detail=False, methods=['get'], url_path='por-empresa-agrupado')
    def evaluacion_empresa(self, request):
        """
        Retorna los registros de EvaluacionDato para una empresa específica, agrupados por fase.
        Requiere el id de la empresa y la gestión de la cookie.
        """
        gestion = self.request.COOKIES.get('gestion')
        empresa_id = request.query_params.get('empresa_id')

        if not all([gestion, empresa_id]):
            return Response(
                {"error": "Los parámetros 'empresa_id' y 'gestion' son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Filtra por el ID de la empresa y la gestión
            queryset = EvaluacionDato.objects.filter(
                empresa__id=empresa_id,
                gestion=gestion
            ).select_related(
                'usuario',
                'empresa',
                'checklist_evaluacion__evaluacion_fase',
            ).order_by('checklist_evaluacion__evaluacion_fase__id')

            # Si no hay datos, retorna un mensaje claro
            if not queryset.exists():
                return Response(
                    {"mensaje": "No se encontraron datos de evaluación para esta empresa en la gestión actual."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Agrupar los datos por fase
            fases_agrupadas = {}
            for dato in queryset:
                fase = dato.checklist_evaluacion.evaluacion_fase
                fase_key = f"{fase.id} - {fase.nombre}"
                
                if fase_key not in fases_agrupadas:
                    fases_agrupadas[fase_key] = {
                        "id": fase.id,
                        "nombre_fase": fase.nombre,
                        "evaluaciones": []
                    }
                
                # Serializar el dato para un formato de respuesta detallado
                evaluacion_data = {
                    "id_evaluacion_dato": dato.id,
                    "puntaje": dato.puntaje,
                    "comentarios": dato.comentarios,
                    "nombre_empresa": dato.empresa.nombre,
                    "empresa_id":dato.empresa.id,
                    "usuario_calificador": dato.usuario.email,
                    "usuario_calificador_id":dato.usuario.id,
                    "checklist": {
                        "id": dato.checklist_evaluacion.id,
                        "nombre": dato.checklist_evaluacion.nombre,
                        "porcentaje_maximo": dato.checklist_evaluacion.porcentaje
                    }
                }
                fases_agrupadas[fase_key]["evaluaciones"].append(evaluacion_data)
            
            # Convertir el diccionario a una lista para la respuesta final
            response_data = list(fases_agrupadas.values())
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Empresa.DoesNotExist:
            return Response(
                {"error": "La empresa especificada no existe."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Ocurrió un error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# ENLACES
# ========================
class EnlacesViewSet(viewsets.ModelViewSet):
    queryset = Enlaces.objects.all().order_by("nombre")
    serializer_class = EnlacesSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "ver_enlaces",
        "retrieve": "ver_enlaces",
        "create": "crear_enlaces",
        "update": "editar_enlaces",
        "partial_update": "editar_enlaces",
        "destroy": "eliminar_enlaces",
        "toggle": "editar_enlaces",
        "list_publicos": "ver_enlaces_publicos",
    }

    def perform_create(self, serializer):
        enlace = serializer.save()
        log_user_action(self.request.user, f"Creó el enlace '{enlace.nombre}'", self.request)

    def perform_update(self, serializer):
        enlace = serializer.save()
        log_user_action(self.request.user, f"Editó el enlace '{enlace.nombre}'", self.request)
    
    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó el enlace '{instance.nombre}'", self.request)
        instance.delete()

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """
        Alterna el estado `is_active` de un enlace.
        """
        enlace = self.get_object()
        enlace.is_active = not enlace.is_active
        enlace.save()
        status_message = "activado" if enlace.is_active else "desactivado"
        log_user_action(request.user, f"Alternó el estado del enlace '{enlace.nombre}' a '{status_message}'", request)
        return Response({'message': f'Enlace ahora está {status_message}.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="publicos")
    def list_publicos(self, request):
        """
        Devuelve solo los enlaces que están activos.
        """
        qs = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)