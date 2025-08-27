# apps/accounts/utils.py
from .models import UserActionLog
from typing import Optional

def get_client_ip(request) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def log_user_action(user, action: str, request=None, extra: dict | None = None):
    UserActionLog.objects.create(
        user=user if (user and getattr(user, "is_authenticated", False)) else None,
        action=action,
        method=getattr(request, "method", "") if request else "",
        path=getattr(request, "path", "") if request else "",
        ip=get_client_ip(request) if request else None,
        extra=extra or {},
    )

def user_has_perm_code(user, code: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    if not user.role_id:
        return False
    return user.role.permissions.filter(code=code).exists()
