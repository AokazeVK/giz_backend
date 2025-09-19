# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from .utils import user_has_perm_code

class HasPermissionMap(BasePermission):
    def has_permission(self, request, view):
        print(f"Action: {getattr(view, 'action', 'N/A')}") # Imprime la acción actual
        code = getattr(view, "required_permission", None)
        if hasattr(view, "action") and hasattr(view, "permission_code_map"):
            action_name = getattr(view, "action")
            code = view.permission_code_map.get(action_name)
            print(f"Mapped Permission Code: {code}") # Imprime el código de permiso mapeado
        
        if not code:
            return True
        
        has_perm = user_has_perm_code(request.user, code)
        print(f"User has permission '{code}': {has_perm}") # Imprime el resultado de la validación
        return has_perm