from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.dtos import AuthSession
from common.exceptions import AuthenticationError


class AuthService:
    """User registration, login, token refresh, and logout with JWT."""

    def __init__(self, *, user_repository, user_service):
        self.user_repository = user_repository
        self.user_service = user_service

    def login(self, *, username, password):
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            raise AuthenticationError("Wrong username or password.")
        return self._session_for(user)

    def register(self, *, username, email, password, first_name="", last_name=""):
        user = self.user_service.register(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return self._session_for(user)

    def refresh(self, *, refresh_token):
        if not refresh_token:
            raise AuthenticationError("Refresh token is missing.", code="token_not_valid")
        try:
            refresh = RefreshToken(refresh_token)
        except TokenError as error:
            raise AuthenticationError(error.args[0], code="token_not_valid")

        user = self.user_repository.get_by_id(refresh.payload.get(api_settings.USER_ID_CLAIM))
        if user is None or not user.is_active:
            raise AuthenticationError("No active account found for this token.")
        return AuthSession(user=user, access=str(refresh.access_token), refresh=None)

    def logout(self, *, refresh_token):
        if not refresh_token:
            return
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return

    def _session_for(self, user):
        refresh = RefreshToken.for_user(user)
        return AuthSession(user=user, access=str(refresh.access_token), refresh=str(refresh))
