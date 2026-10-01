"""
Authenticate WebSocket connections using JWT tokens stored in cookies,
falling back to AnonymousUser if no valid token is found.
"""
from http.cookies import SimpleCookie

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError


class JwtCookieAuthMiddleware(BaseMiddleware):
    """Extract JWT from cookies and authenticate the WebSocket connection."""
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        token = _access_token(scope)
        scope["user"] = await _authenticate(token)
        return await super().__call__(scope, receive, send)


def _access_token(scope):
    """Extract access token from Cookie header; return None if not found."""
    headers = scope.get("headers")
    if headers is None:
        headers = []
    cookie_header = ""
    for name, value in headers:
        if name == b"cookie":
            cookie_header = value.decode()

    cookies = SimpleCookie()
    cookies.load(cookie_header)
    morsel = cookies.get(settings.AUTH_COOKIE_ACCESS)
    if morsel is None:
        return None
    return morsel.value


@database_sync_to_async
def _authenticate(token):
    """Validate token and return user; return AnonymousUser if invalid or missing."""
    if not token:
        return AnonymousUser()
    authentication = JWTAuthentication()
    try:
        validated_token = authentication.get_validated_token(token)
        return authentication.get_user(validated_token)
    except (TokenError, AuthenticationFailed):
        return AnonymousUser()
