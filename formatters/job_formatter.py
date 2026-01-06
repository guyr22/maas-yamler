from abc import ABC, abstractmethod
from typing import Dict, Any, List


class JobFormatter(ABC):
    @staticmethod
    def convert_number_to_seconds(number: str) -> str:
        return f"{number}s"

    @staticmethod
    def create_static_configs(targets: List[str]) -> List[Dict[str, Any]]:
        return [{"targets": targets}]

    @classmethod
    def format_common_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if data.get("scheme", "http") == "https":
            data["tls_config"] = {"insecure_skip_verify": True}
        
        if "scrape_timeout" in data:
            data["scrape_timeout"] = cls.convert_number_to_seconds(data["scrape_timeout"])

        if "scrape_interval" in data:
            data["scrape_interval"] = cls.convert_number_to_seconds(data["scrape_interval"])

        if "labels" in data:
            data['static_configs'] = [{'labels': data.pop("labels")}]

        return data


    @classmethod
    @abstractmethod
    def format_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass