from django.db.models import Min

from apps.runs.models import PersonalRecord
from common.repositories import BaseRepository


class PersonalRecordRepository(BaseRepository[PersonalRecord]):
    """Query personal records by user/run; track best times per distance."""
    model = PersonalRecord

    def list_of_run(self, run):
        return list(self.model.objects.filter(run=run))

    def list_of_user_with_run(self, user):
        records = self.model.objects.filter(user=user)
        return list(records.select_related("run").order_by("time_s", "achieved_at"))

    def best_times_of_user_before(self, user, before):
        records = self.model.objects.filter(user=user, run__started_at__lt=before)
        return self._best_times(records)

    def replace_of_run(self, run, records):
        self.model.objects.filter(run=run).delete()
        for record in records:
            record.full_clean(validate_constraints=False)
        return self.model.objects.bulk_create(records)

    def _best_times(self, records):
        rows = records.values("distance").annotate(best=Min("time_s"))
        best_by_distance = {}
        for row in rows:
            best_by_distance[row["distance"]] = row["best"]
        return best_by_distance
