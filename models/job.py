from typing import Dict, Any, Optional
from enums.job_types import JobType
from pydantic import BaseModel
from enums.event_actions import EventAction


class JobEvent(BaseModel):
    action: EventAction
    collector_cluster: str
    maas_pool: str
    job_name: str
    job_type: JobType
    job_data: Optional[Dict[str, Any]] = None

    def __str__(self):
        return f"{self.action} {self.collector_cluster} {self.maas_pool} {self.job_name} {self.job_type} {self.job_data}"