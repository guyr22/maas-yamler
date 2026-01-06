import pytest
from unittest.mock import MagicMock, patch
import json
from enums.event_actions import EventAction
from enums.job_types import JobType

# Need to reload consumer module if we advanced mocking config in conftest
# but conftest runs first so it should be fine.
from consumer import ConsumerService


@pytest.fixture
def consumer_service():
    with patch("consumer.Consumer") as mock_consumer_cls:
        with patch("consumer.GitPrometheusManager") as mock_pm_cls:
            service = ConsumerService()
            service.consumer = MagicMock()

            # Setup PrometheusManager mock
            service.prometheus_manager = MagicMock()

            yield service


def test_process_event_success(consumer_service, sample_job_data):
    payload = {
        "action": EventAction.CREATE,
        "collector_cluster": "cluster-1",
        "maas_pool": "pool-1",
        "job_name": "test-job",
        "job_type": JobType.GENERAL,
        "job_data": sample_job_data,
    }

    # Mocking get_formatter
    with patch("consumer.get_formatter") as mock_get_formatter:
        mock_formatter = MagicMock()
        mock_formatter.format_job.return_value = {"formatted": "data"}
        mock_get_formatter.return_value = mock_formatter

        consumer_service._process_event(payload)

        # Verify formatting was called
        mock_formatter.format_job.assert_called()

        # Verify update content was called
        consumer_service.prometheus_manager.update_content.assert_called_with(
            action=EventAction.CREATE,
            job_data={"formatted": "data"},
            job_name="test-job",
            yaml_filename="cluster-1/pool-1/pool-1-collector-values.yaml",
        )


def test_process_event_delete(consumer_service):
    payload = {
        "action": EventAction.DELETE,
        "collector_cluster": "c1",
        "maas_pool": "p1",
        "job_name": "job1",
        "job_type": JobType.GENERAL,
        "job_data": {},
    }

    with patch("consumer.get_formatter") as mock_get_formatter:
        consumer_service._process_event(payload)

        # Formatter should NOT be called for DELETE (based on code reading logic)
        # consumer.py lines 84: if event.action in [EventAction.CREATE, EventAction.UPDATE]:
        mock_get_formatter.assert_not_called()

        consumer_service.prometheus_manager.update_content.assert_called()


def test_process_event_error_handling(consumer_service):
    # Simulate error in update_content
    consumer_service.prometheus_manager.update_content.side_effect = Exception(
        "Update failed"
    )

    payload = {
        "action": EventAction.CREATE,
        "collector_cluster": "c1",
        "maas_pool": "p1",
        "job_name": "j1",
        "job_type": JobType.GENERAL,
        "job_data": {},
    }

    # Should catch exception and log error, not raise
    with patch("consumer.get_formatter"):
        consumer_service._process_event(payload)


def test_consumer_loop_message_processing(consumer_service):
    # Test the start loop processing a message
    service = consumer_service

    # Mock message
    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    mock_msg.value.return_value = json.dumps(
        {
            "action": EventAction.CREATE,
            "collector_cluster": "c1",
            "maas_pool": "p1",
            "job_name": "j1",
            "job_type": JobType.GENERAL,
            "job_data": {},
        }
    ).encode("utf-8")

    service.consumer.poll.side_effect = [mock_msg, Exception("Stop Loop")]

    # We use a side effect exception to break the infinite loop for testing
    # Or we can mock _process_event to set running=False

    service._process_event = MagicMock(
        side_effect=lambda x: setattr(service, "running", False)
    )

    service.start()

    service._process_event.assert_called_once()
    service.consumer.commit.assert_called()


def test_consumer_seek_on_error(consumer_service):
    # Test that exception in processing triggers rollback and seek
    service = consumer_service

    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    mock_msg.value.return_value = b"invalid json"  # Will cause json.loads error
    mock_msg.topic.return_value = "topic"
    mock_msg.partition.return_value = 0
    mock_msg.offset.return_value = 100

    service.consumer.poll.return_value = mock_msg

    # Break loop after one iteration
    def stop_loop(*args, **kwargs):
        service.running = False
        return mock_msg

    service.consumer.poll.side_effect = stop_loop

    service.start()

    service.prometheus_manager.rollback.assert_called()
    service.consumer.seek.assert_called()
