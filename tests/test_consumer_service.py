import pytest
from unittest.mock import MagicMock, patch
from consumer import ConsumerService
from enums.event_actions import EventAction
# from models.job import JobEvent
from exceptions.consumer_seek_error import ConsumerSeekError
from confluent_kafka import KafkaError


@pytest.fixture
def mock_consumer():
    with patch("consumer.Consumer") as mock:
        yield mock


@pytest.fixture
def mock_prometheus_manager():
    with patch("consumer.GitPrometheusManager") as mock:
        yield mock


@pytest.fixture
def consumer_service(mock_consumer, mock_prometheus_manager):
    service = ConsumerService()
    service.consumer = mock_consumer.return_value
    service.prometheus_manager = mock_prometheus_manager.return_value
    return service


def test_start_success(consumer_service, mock_consumer):
    consumer_service.running = False

    # We need to simulate the loop running once then stopping
    def side_effect(*args, **kwargs):
        consumer_service.running = False  # Stop loop after first poll
        return None

    consumer_service.consumer.poll.side_effect = side_effect

    consumer_service.start()

    mock_consumer.assert_called_once()
    consumer_service.consumer.subscribe.assert_called_once()


def test_process_event_create_success(consumer_service):
    event_data = {
        "action": "create",
        "job_type": "general",  # Assuming 'active_job' maps to a formatter causing no error or mocked
        "job_name": "test_job",
        "maas_pool": "pool1",
        "collector_cluster": "cluster1",
        "data": {"some": "data"},
    }

    # Mocking get_formatter to avoid dependency on real formatters in this unit test
    with patch("consumer.get_formatter") as mock_get_formatter:
        mock_formatter = MagicMock()
        mock_formatter.format_job.return_value = {"formatted": "data"}
        mock_get_formatter.return_value = mock_formatter

        consumer_service._process_event(event_data)

        mock_get_formatter.assert_called_once()
        consumer_service.prometheus_manager.update_content.assert_called_once_with(
            action=EventAction.CREATE,
            job_data={"formatted": "data"},
            job_name="test_job",
            yaml_filename="cluster1/pool1/pool1-collector-values.yaml",
        )


def test_process_event_error_handling(consumer_service):
    # Simulate an error during processing
    with patch("consumer.get_formatter", side_effect=Exception("Format error")):
        consumer_service._process_event({"action": "CREATE", "job_type": "unknown"})
        # Should log error and not crash, not call update_content
        consumer_service.prometheus_manager.update_content.assert_not_called()


def test_kafka_error_handling(consumer_service):
    # Setup mock message with error
    mock_msg = MagicMock()
    mock_msg.error.return_value = MagicMock()
    mock_msg.error.return_value.code.return_value = KafkaError._PARTITION_EOF

    consumer_service.consumer.poll.return_value = mock_msg

    # We run the loop for one iteration
    consumer_service.running = True

    def stop_loop(*args, **kwargs):
        consumer_service.running = False
        return mock_msg

    consumer_service.consumer.poll.side_effect = stop_loop

    consumer_service.start()
    # Should handle EOF gracefully (logging)


def test_seek_success(consumer_service):
    tp = MagicMock()
    consumer_service.seek(tp)
    consumer_service.consumer.seek.assert_called_once_with(tp)


def test_seek_failure(consumer_service):
    consumer_service.consumer.seek.side_effect = Exception("Seek error")
    with pytest.raises(ConsumerSeekError):
        consumer_service.seek(MagicMock())
