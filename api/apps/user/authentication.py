"""
Authenticates requests using JWT from httpOnly cookies with CSRF protection.
"""
from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Reads JWT from the access cookie and validates CSRF token."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        enforce_csrf(request)
        return user, validated_token


def _empty_response(request):
    return None


def enforce_csrf(request):
    """Verify CSRF token from the request, raise PermissionDenied if invalid."""
    check = CSRFCheck(_empty_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF check failed: {reason}")
