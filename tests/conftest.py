import pytest
from unittest.mock import MagicMock
import sys

# Mock config before importing modules that use it
mock_config = {
    "kafka": {
        "servers": "localhost:9092",
        "username": "test_user",
        "topic": "test_topic",
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "PLAIN",
        "sasl_username": "user",
        "sasl_password": "password",
    },
    "git": {
        "repo_url": "http://git.url/repo.git",
        "local_path": "/tmp/repo",
        "branch": "main",
    },
    "general": {"collectors_namespace": "monitoring", "env": "test"},
    "certs": {
        "ca_file": "/path/to/ca",
        "cert_file": "/path/to/cert",
        "key_file": "/path/to/key",
    },
    "logs": {"base_level": "DEBUG", "logstash": {"enabled": False, "lebel": "DEBUG", "host": "", "port": "", "transport_type": ""}, "console": {"level": "DEBUG", "format": "%(asctime)-24s\t%(levelname)-5s\t%(name)-12s\t%(message)s"}}
}

# Mock config.constants
constants_mock = MagicMock()
constants_mock.PROD_ENV = "production"
constants_mock.CONFIG_YAML_NAME = "config.yaml"
constants_mock.BLACKBOX_CONFIGURATION = [
    {
        "source_labels": ["__address__"],
        "seperator": ";",
        "regex": "(.*)",
        "target_label": "__param_target",
        "replacement": "$1",
        "action": "replace",
    },
    {
        "source_labels": ["__param_target"],
        "seperator": ":",
        "regex": "(.*)",
        "target_label": "instance",
        "replacement": "$1",
        "action": "replace",
    },
    {
        "seperator": ";",
        "regex": "(.*)",
        "target_label": "__address__",
        "action": "replace",
    },
]
sys.modules["config.constants"] = constants_mock

# Mock config module
module_mock = MagicMock()
module_mock.KAFKA_CONFIG = mock_config["kafka"]
module_mock.GIT_CONFIG = mock_config["git"]
module_mock.GENERAL_CONFIG = mock_config["general"]
module_mock.CERTS_CONFIG = mock_config["certs"]
module_mock.LOGS_CONFIG = mock_config["logs"]
# Ensure it mimics a package structure if needed, or just attributes
sys.modules["config"] = module_mock

from enums.job_types import JobType
from enums.event_actions import EventAction


@pytest.fixture
def sample_job_data():
    return {
        "metrics_path": "/metrics",
        "scrape_interval": "1m",
        "scrape_timeout": "10s",
        "scheme": "http",
        "targets": ["localhost:8080"],
    }


@pytest.fixture
def sample_event_payload(sample_job_data):
    return {
        "action": EventAction.CREATE,
        "collector_cluster": "cluster-1",
        "maas_pool": "pool-1",
        "job_name": "test-job",
        "job_type": JobType.GENERAL,
        "job_data": sample_job_data,
    }
