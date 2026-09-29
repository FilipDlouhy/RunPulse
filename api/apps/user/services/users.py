from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.user.models import User
from common.exceptions import NotFoundError, ValidationFailedError


class UserService:
    def __init__(self, *, user_repository):
        self.user_repository = user_repository

    def get_by_id(self, *, user_id):
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    @transaction.atomic
    def register(self, *, username, email, password, first_name="", last_name=""):
        errors = {}
        if self.user_repository.exists_by_username(username):
            errors["username"] = ["A user with this username already exists."]
        if self.user_repository.exists_by_email(email):
            errors["email"] = ["A user with this email already exists."]
        if errors:
            raise ValidationFailedError(errors)

        user = User(
            username=User.normalize_username(username),
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            role=User.Role.RUNNER,
        )
        try:
            validate_password(password, user)
        except DjangoValidationError as error:
            raise ValidationFailedError({"password": list(error.messages)})

        user.set_password(password)
        return self.user_repository.save(user)
