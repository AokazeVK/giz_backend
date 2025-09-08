# comunidad/middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


@database_sync_to_async
def get_user_from_jwt(token_str):
    """
    Valida el token con Simple JWT y devuelve el usuario.
    """
    try:
        # Valida el token con SimpleJWT (firma, expiración, etc.)
        validated_token = UntypedToken(token_str)
        user_id = validated_token.get("user_id")

        if user_id:
            return User.objects.get(id=user_id)
    except (TokenError, User.DoesNotExist):
        pass
    return AnonymousUser()


class JwtAuthMiddleware:
    """
    Middleware que autentica al usuario en WebSocket usando un JWT en cookie httponly.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        # Buscar cookie "access_token"
        cookie_header = next(
            (value for name, value in scope.get("headers", []) if name == b"cookie"),
            None,
        )

        if cookie_header:
            cookie_string = cookie_header.decode()
            token = None
            for cookie in cookie_string.split(";"):
                cookie_name, *cookie_value = cookie.split("=", 1)
                if cookie_name.strip() == "access_token":
                    token = cookie_value[0].strip()
                    break

            if token:
                scope["user"] = await get_user_from_jwt(token)
                print(f"[JwtAuthMiddleware] Usuario autenticado: {scope['user']}")

        return await self.inner(scope, receive, send)
