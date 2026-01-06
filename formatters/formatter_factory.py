from enums.job_types import JobType
from formatters.blackbox_job_formatter import BlackboxJobFormatter
from formatters.general_job_formatter import GeneralJobFormatter
from formatters.http_sd_job_formatter import HttpSDJobFormatter
from formatters.job_formatter import JobFormatter
from typing import Type, Dict


FORMATTERS: Dict[JobType, Type[JobFormatter]] = {
    JobType.BLACKBOX: BlackboxJobFormatter,
    JobType.GENERAL: GeneralJobFormatter,
    JobType.HTTP_SD: HttpSDJobFormatter,
}


def get_formatter(job_type: JobType) -> Type[JobFormatter]:
    formatter = FORMATTERS.get(job_type)
    if formatter is None:
        raise ValueError(f"Invalid job type: {job_type}")
    return formatter