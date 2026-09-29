from apps.runs.models import DeadLetter
from common.repositories import BaseRepository


class DeadLetterRepository(BaseRepository[DeadLetter]):
    model = DeadLetter

    def list_recent(self, limit):
        return list(self.model.objects.all()[:limit])
