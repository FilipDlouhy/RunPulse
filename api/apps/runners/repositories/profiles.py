from apps.runners.models import RunnerProfile
from common.repositories import BaseRepository


class RunnerProfileRepository(BaseRepository[RunnerProfile]):
    model = RunnerProfile

    def get_by_user(self, user):
        return self.model.objects.filter(user=user).first()

    def update_or_create_for_user(self, user, fields):
        profile, _created = self.model.objects.update_or_create(user=user, defaults=fields)
        return profile
