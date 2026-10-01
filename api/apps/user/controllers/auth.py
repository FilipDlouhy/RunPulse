from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import ViewSet

from apps.user.authentication import CookieJWTAuthentication
from apps.user.cookies import delete_auth_cookies, set_auth_cookies
from apps.user.dtos import LoginRequestSerializer, RegisterUserRequestSerializer, UserResponseSerializer
from apps.user.services import auth_service, user_service


class AuthController(ViewSet):
    """API endpoints for user registration, login, token refresh, logout, and profile retrieval."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @action(detail=False, methods=["post"], throttle_classes=[ScopedRateThrottle])
    def register(self, request):
        serializer = RegisterUserRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = auth_service.register(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        response = Response(UserResponseSerializer(session.user).data, status=status.HTTP_201_CREATED)
        set_auth_cookies(request, response, session.access, session.refresh)
        return response

    @action(detail=False, methods=["post"], throttle_classes=[ScopedRateThrottle])
    def login(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = auth_service.login(username=data["username"], password=data["password"])
        response = Response(UserResponseSerializer(session.user).data)
        set_auth_cookies(request, response, session.access, session.refresh)
        return response

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        session = auth_service.refresh(refresh_token=request.COOKIES.get(settings.AUTH_COOKIE_REFRESH))
        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_auth_cookies(request, response, session.access, session.refresh)
        return response

    @action(detail=False, methods=["post"])
    def logout(self, request):
        auth_service.logout(refresh_token=request.COOKIES.get(settings.AUTH_COOKIE_REFRESH))
        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_auth_cookies(response)
        return response

    @action(
        detail=False,
        methods=["get"],
        authentication_classes=[CookieJWTAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        user = user_service.get_by_id(user_id=request.user.id)
        return Response(UserResponseSerializer(user).data)
