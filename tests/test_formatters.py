import pytest
from enums.job_types import JobType
from formatters.formatter_factory import get_formatter
from formatters.general_job_formatter import GeneralJobFormatter
from formatters.blackbox_job_formatter import BlackboxJobFormatter
from formatters.http_sd_job_formatter import HttpSDJobFormatter
from config import CERTS_CONFIG


def test_get_formatter_success():
    assert get_formatter(JobType.GENERAL) == GeneralJobFormatter
    assert get_formatter(JobType.BLACKBOX) == BlackboxJobFormatter
    assert get_formatter(JobType.HTTP_SD) == HttpSDJobFormatter


def test_get_formatter_invalid():
    with pytest.raises(ValueError):
        get_formatter("unknown")


class TestGeneralJobFormatter:
    def test_format_basic(self):
        input_data = {
            "job_name": "test",
            "scrape_interval": 60,
            "scrape_timeout": 30,
            "targets": ["localhost:9090"],
        }

        output = GeneralJobFormatter.format_job(input_data)

        assert output["job_name"] == "test"
        assert output["scrape_interval"] == "60s"
        assert output["scrape_timeout"] == "30s"
        assert output["static_configs"][0]["targets"] == ["localhost:9090"]

    def test_format_certs(self):
        input_data = {"job_name": "test", "certs": True}

        # Patching or assuming global config loaded.
        # Ideally we'd patch 'formatters.general_job_formatter.CERTS_CONFIG' but it is imported directly.
        # However, we can assert based on what keys are present.

        output = GeneralJobFormatter.format_job(input_data)

        assert "tls_config" in output
        assert output["tls_config"]["ca_file"] == CERTS_CONFIG["ca_file"]


class TestBlackboxJobFormatter:
    def test_format_basic(self):
        input_data = {
            "job_name": "blackbox",
            "module": "http_2xx",
            "metrics_path": "/probe",
            "host": "prometheus-blackbox-exporter",
            "targets": ["example.com"],
        }

        output = BlackboxJobFormatter.format_job(input_data)

        assert output["metrics_path"] == "/probe"
        assert output["params"]["module"] == ["http_2xx"]
        assert output["static_configs"][0]["targets"] == ["example.com"]

        # Verify blackbox config relay
        # NOTE: logic copies constant then sets replacement
        assert (
            output["relabel_configs"][2]["replacement"]
            == "prometheus-blackbox-exporter"
        )


class TestHttpSDJobFormatter:
    def test_format_basic(self):
        input_data = {
            "job_name": "httpsd",
            "url_endpoints": ["http://discovery"],
            "refresh_interval": 60,
        }

        output = HttpSDJobFormatter.format_job(input_data)

        assert output["http_sd_configs"][0]["url"] == "http://discovery"
        # The logic converts number to seconds suffix?
        # Looking at code: cls.convert_number_to_seconds (inherited?)
        # Base JobFormatter isn't visible in my context but let's assume it appends 's' if int.
        assert output["http_sd_configs"][0]["refresh_interval"] == "60s"

    def test_format_auth_and_certs(self):
        input_data = {
            "job_name": "httpsd",
            "url_endpoints": ["http://discovery"],
            "basic_auth": {"username": "u", "password": "p"},
            "certs": True,
        }

        output = HttpSDJobFormatter.format_job(input_data)

        assert output["http_sd_configs"][0]["basic_auth"] == {
            "username": "u",
            "password": "p",
        }
        assert output["tls_config"]["ca_file"] == CERTS_CONFIG["ca_file"]
