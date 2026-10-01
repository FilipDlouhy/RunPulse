"""
Application-level exceptions with HTTP status codes and consistent API response format.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

AUTHENTICATE_HEADER = 'Bearer realm="api"'


class ApplicationError(Exception):
    """Base exception for application errors, converts to HTTP response."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, *, code=None):
        super().__init__(message)
        self.message = message
        self.code = code

    def to_data(self):
        data = {"detail": self.message}
        if self.code:
            data["code"] = self.code
        return data


class ValidationFailedError(ApplicationError):
    """Input validation failed; returns field errors as-is."""

    def __init__(self, errors):
        super().__init__("Invalid input.")
        self.errors = errors

    def to_data(self):
        return self.errors


class NotFoundError(ApplicationError):
    """Resource not found."""

    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(ApplicationError):
    """Resource already exists or operation violates a constraint."""

    status_code = status.HTTP_409_CONFLICT


class AuthenticationError(ApplicationError):
    """Request lacks valid credentials."""

    status_code = status.HTTP_401_UNAUTHORIZED


class ServiceUnavailableError(ApplicationError):
    """Dependency is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


def custom_exception_handler(exc, context):
    """Convert ApplicationError and Django ValidationError to REST responses."""
    if isinstance(exc, ApplicationError):
        response = Response(exc.to_data(), status=exc.status_code)
        if isinstance(exc, AuthenticationError):
            response["WWW-Authenticate"] = AUTHENTICATE_HEADER
        return response
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "error_dict"):
            data = exc.message_dict
        else:
            data = {"detail": exc.messages}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    return exception_handler(exc, context)
