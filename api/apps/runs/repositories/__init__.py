from .dead_letters import DeadLetterRepository
from .records import PersonalRecordRepository
from .runs import RunRepository
from .samples import SampleRepository
from .summaries import RunSummaryRepository
from .usage import UsageHourlyRepository

run_repository = RunRepository()
sample_repository = SampleRepository()
run_summary_repository = RunSummaryRepository()
personal_record_repository = PersonalRecordRepository()
dead_letter_repository = DeadLetterRepository()
usage_hourly_repository = UsageHourlyRepository()

__all__ = [
    "dead_letter_repository",
    "personal_record_repository",
    "run_repository",
    "run_summary_repository",
    "sample_repository",
    "usage_hourly_repository",
]
