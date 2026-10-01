"""
Celery task to analyze a completed run using the run-analysis pipeline
with automatic retries and failure handling.
"""
import logging

from celery import shared_task
from django.conf import settings

from .services import analysis_service, run_analysis_pipeline
from .services.pipeline_runner import PipelineAbort

logger = logging.getLogger(__name__)


def retry_countdown(retries):
    """Map retry attempt count to delay seconds from config."""
    delays = settings.PIPELINE_RETRY_DELAYS
    if retries < len(delays):
        return delays[retries]
    return delays[-1]


@shared_task(bind=True, max_retries=2)
def analyze_run(self, run_id):
    """Analyze a run if it's in the correct state; mark failed on abort or max retries."""
    if not analysis_service.can_analyze(run_id=run_id):
        return
    try:
        run_analysis_pipeline.run(run_id)
    except PipelineAbort:
        analysis_service.mark_failed(run_id=run_id)
        return
    except Exception:
        logger.warning(
            "Analysis of run %s failed (attempt %s/%s).",
            run_id, self.request.retries + 1, self.max_retries + 1, exc_info=True,
        )
        try:
            raise self.retry(countdown=retry_countdown(self.request.retries))
        except self.MaxRetriesExceededError:
            analysis_service.mark_failed(run_id=run_id)
            return

