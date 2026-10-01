"""
JWT token storage in httpOnly cookies, CSRF-protected and same-site only.
"""
from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework_simplejwt.settings import api_settings

ACCESS_COOKIE_PATH = "/"             # access token available app-wide
REFRESH_COOKIE_PATH = "/api/auth/"   # refresh token only at auth endpoint


def set_auth_cookies(request, response, access, refresh=None):
    """Set JWT tokens in httpOnly cookies and generate a CSRF token for the frontend."""
    _set_cookie(
        response,
        settings.AUTH_COOKIE_ACCESS,
        access,
        api_settings.ACCESS_TOKEN_LIFETIME,
        ACCESS_COOKIE_PATH,
    )
    if refresh is not None:
        _set_cookie(
            response,
            settings.AUTH_COOKIE_REFRESH,
            refresh,
            api_settings.REFRESH_TOKEN_LIFETIME,
            REFRESH_COOKIE_PATH,
        )
    get_token(request)


def delete_auth_cookies(response):
    response.delete_cookie(
        settings.AUTH_COOKIE_ACCESS,
        path=ACCESS_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_COOKIE_REFRESH,
        path=REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def _set_cookie(response, name, value, lifetime, path):
    response.set_cookie(
        name,
        value,
        max_age=lifetime,
        path=path,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
