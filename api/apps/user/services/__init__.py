from apps.user.repositories import user_repository

from .auth import AuthService
from .users import UserService

user_service = UserService(user_repository=user_repository)
auth_service = AuthService(user_repository=user_repository, user_service=user_service)

__all__ = ["auth_service", "user_service"]
