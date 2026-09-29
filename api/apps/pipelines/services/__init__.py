from apps.gym_admin.repositories import device_repository
from apps.pipelines.repositories import pipeline_run_repository, pipeline_step_repository
from apps.runners.repositories import runner_profile_repository
from apps.runs.repositories import (
    dead_letter_repository,
    personal_record_repository,
    run_repository,
    run_summary_repository,
    sample_repository,
)

from .pipeline_runner import PipelineRunner
from .run_analysis.pipeline import RunAnalysisPipeline
from .run_analysis.results import AnalysisService
from .tech import TechService

pipeline_runner = PipelineRunner(
    pipeline_run_repository=pipeline_run_repository,
    pipeline_step_repository=pipeline_step_repository,
)
analysis_service = AnalysisService(
    run_repository=run_repository,
    run_summary_repository=run_summary_repository,
    personal_record_repository=personal_record_repository,
    device_repository=device_repository,
)
tech_service = TechService(
    dead_letter_repository=dead_letter_repository,
    pipeline_run_repository=pipeline_run_repository,
    pipeline_step_repository=pipeline_step_repository,
)
run_analysis_pipeline = RunAnalysisPipeline(
    pipeline_runner=pipeline_runner,
    run_repository=run_repository,
    sample_repository=sample_repository,
    runner_profile_repository=runner_profile_repository,
    analysis_service=analysis_service,
)

__all__ = [
    "analysis_service",
    "run_analysis_pipeline",
    "tech_service",
]
