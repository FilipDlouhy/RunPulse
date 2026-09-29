from apps.user.models import User
from common.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_runner_by_username(self, username):
        return self.model.objects.filter(role=User.Role.RUNNER, username=username).first()

    def get_or_create_by_username(self, username):
        user, _ = self.model.objects.get_or_create(username=username)
        return user

    def exists_by_username(self, username):
        return self.model.objects.filter(username=username).exists()

    def exists_by_email(self, email):
        return self.model.objects.filter(email__iexact=email).exists()
