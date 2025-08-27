# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from .utils import user_has_perm_code

class HasPermissionMap(BasePermission):
    """
    - Para ViewSets: define `permission_code_map = {action: 'perm_code'}`.
    - Para APIViews: define `required_permission = 'perm_code'`.
    Si no hay código requerido, permite por defecto.
    """
    def has_permission(self, request, view):
        code = getattr(view, "required_permission", None)
        if hasattr(view, "action") and hasattr(view, "permission_code_map"):
            code = view.permission_code_map.get(getattr(view, "action"))
        if not code:
            return True
        return user_has_perm_code(request.user, code)
