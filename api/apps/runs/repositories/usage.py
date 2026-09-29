from django.db.models import Sum
from django.db.models.functions import ExtractHour, ExtractIsoWeekDay

from apps.runs.models import UsageHourly
from common.repositories import BaseRepository


class UsageHourlyRepository(BaseRepository[UsageHourly]):
    model = UsageHourly

    def seconds_by_weekday_hour(self, *, since, until, tz):
        return list(
            self.model.objects.filter(bucket__gte=since, bucket__lt=until)
            .annotate(weekday=ExtractIsoWeekDay("bucket", tzinfo=tz), hour=ExtractHour("bucket", tzinfo=tz))
            .values("weekday", "hour")
            .annotate(total_seconds=Sum("seconds"))
        )
