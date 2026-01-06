import pytest
from formatters.formatter_factory import get_formatter
from formatters.general_job_formatter import GeneralJobFormatter
from formatters.blackbox_job_formatter import BlackboxJobFormatter
from formatters.http_sd_job_formatter import HttpSDJobFormatter
from enums.job_types import JobType


def test_formatter_factory():
    assert get_formatter(JobType.GENERAL) == GeneralJobFormatter
    assert get_formatter(JobType.BLACKBOX) == BlackboxJobFormatter
    assert get_formatter(JobType.HTTP_SD) == HttpSDJobFormatter

    with pytest.raises(ValueError):
        get_formatter("INVALID_TYPE")


def test_general_job_formatter(sample_job_data):
    formatted = GeneralJobFormatter.format_job(sample_job_data.copy())

    # Check structure
    assert "targets" not in formatted
    assert formatted["static_configs"][0]["targets"] == sample_job_data["targets"]
    assert formatted["metrics_path"] == "/metrics"


def test_general_job_formatter_tls():
    data = {
        "targets": ["host:port"],
        "certs": True,
        "metrics_path": "/metrics",  # Required to be poppable or processed
    }
    # Mocking common fields requirement if any. Assuming simplistic for now or that base class handles it.
    # Base JobFormatter isn't visible here but format_common_fields usually handles metrics_path etc.
    # We'll need to make sure 'metrics_path' is in input if base class expects it.

    formatted = GeneralJobFormatter.format_job(data)
    assert "tls_config" in formatted
    assert formatted["tls_config"]["ca_file"] == "/path/to/ca"


def test_blackbox_job_formatter():
    data = {
        "module": "http_2xx",
        "metrics_path": "/probe",
        "targets": ["example.com"],
        "host": "prometheus-blackbox-exporter:9115",
        "scrape_interval": "1m",
    }
    formatted = BlackboxJobFormatter.format_job(data)

    assert formatted["metrics_path"] == "/probe"
    # Verify module param structure
    assert formatted["params"]["module"] == ["http_2xx"]
    # Verify relabel configs for replacement
    assert (
        formatted["relabel_configs"][2]["replacement"]
        == "prometheus-blackbox-exporter:9115"
    )


def test_http_sd_job_formatter():
    data = {
        "url_endpoints": ["http://discovery.example.com"],
        "refresh_interval": "5m",
        "basic_auth": {"username": "user", "password": "pass"},
    }
    # http_sd might expect metrics_path or other common fields if it calls format_common_fields
    # Looking at code: yes, it calls cls.format_common_fields(data)
    # We should add minimal common fields
    data["metrics_path"] = "/metrics"

    formatted = HttpSDJobFormatter.format_job(data)

    assert len(formatted["http_sd_configs"]) == 1
    config = formatted["http_sd_configs"][0]
    assert config["url"] == "http://discovery.example.com"
    assert config["basic_auth"]["username"] == "user"
    assert config["refresh_interval"] == 300  # 5m converted to seconds
