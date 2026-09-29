import time

from django.db import transaction

from apps.pipelines.models import PipelineRun, PipelineStep


class PipelineAbort(Exception):
    pass


def elapsed_ms(started):
    return round((time.monotonic() - started) * 1000)


class PipelineRunner:
    def __init__(self, *, pipeline_run_repository, pipeline_step_repository):
        self.pipeline_run_repository = pipeline_run_repository
        self.pipeline_step_repository = pipeline_step_repository

    def run(self, name, steps, ctx, *, run_id=None):
        pipeline_run = PipelineRun(name=name, run_id=run_id)
        self.pipeline_run_repository.save(pipeline_run, validate=False)
        for order, step in enumerate(steps, start=1):
            log = PipelineStep(pipeline_run=pipeline_run, order=order, name=step.__name__)
            self.pipeline_step_repository.save(log, validate=False)
            started = time.monotonic()
            try:
                with transaction.atomic():
                    ctx = step(ctx)
            except Exception as error:
                duration_ms = elapsed_ms(started)
                log.fail(error, duration_ms)
                self.pipeline_step_repository.save(log, update_fields=["status", "duration_ms", "error"], validate=False)
                pipeline_run.fail(step.__name__)
                self.pipeline_run_repository.save(
                    pipeline_run, update_fields=["status", "finished_at", "failed_step"], validate=False
                )
                raise
            duration_ms = elapsed_ms(started)
            log.done(duration_ms)
            self.pipeline_step_repository.save(log, update_fields=["status", "duration_ms"], validate=False)
        pipeline_run.done()
        self.pipeline_run_repository.save(pipeline_run, update_fields=["status", "finished_at"], validate=False)
        return ctx
