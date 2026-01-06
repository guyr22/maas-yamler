import pytest
from pydantic import ValidationError
from models.job import JobEvent
from enums.job_types import JobType
from enums.event_actions import EventAction


def test_job_event_valid(sample_event_payload):
    event = JobEvent(**sample_event_payload)
    assert event.action == EventAction.CREATE
    assert event.job_name == "test-job"
    assert event.job_type == JobType.GENERAL
    assert event.job_data["targets"] == ["localhost:8080"]


def test_job_event_missing_field(sample_event_payload):
    del sample_event_payload["action"]
    with pytest.raises(ValidationError):
        JobEvent(**sample_event_payload)


def test_job_event_str_representation(sample_event_payload):
    event = JobEvent(**sample_event_payload)
    assert "test-job" in str(event)
    assert "cluster-1" in str(event)
