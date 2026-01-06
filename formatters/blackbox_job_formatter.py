from typing import Dict, Any
from config.constants import BLACKBOX_CONFIGURATION
from formatters.job_formatter import JobFormatter


class BlackboxJobFormatter(JobFormatter):
    @staticmethod
    def get_blackbox_config(host: str):
        blackbox_config = BLACKBOX_CONFIGURATION.copy()
        blackbox_config[2]["replacement"] = host

        return blackbox_config

    @classmethod
    def format_job(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        data = cls.format_common_fields(data)
        data['params'] = {"module": [data.pop("module")]}
        data['metrics_path'] = data.pop("metrics_path")
        data['static_configs'] = data.get("static_configs", [{}])
        data['static_configs'][0]['targets'] = data.pop("targets", [])
        data['relabel_configs'] = cls.get_blackbox_config(data.pop("host"))

        return data