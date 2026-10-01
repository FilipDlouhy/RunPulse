from apps.runs.models import RunSummary
from common.repositories import BaseRepository


class RunSummaryRepository(BaseRepository[RunSummary]):
    """Fetch run analysis summaries."""
    model = RunSummary

    def get_by_run(self, run):
        return self.model.objects.filter(run=run).first()
