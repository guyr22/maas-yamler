from abc import ABC, abstractmethod
from typing import Dict, Any
from ruamel.yaml import YAML
from utils.logger import create_logger
from enums.event_actions import EventAction


class PrometheusManager(ABC):
    def __init__(self):
        self.logger = create_logger("prometheus_manager")
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    @abstractmethod
    def load(self, yaml_filename: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save(self, content: Dict[str, Any], yaml_filename: str, prom_config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def reload(self):
        pass

    @abstractmethod
    def rollback(self):
        pass

    @staticmethod
    def get_prometheus_config(content: Dict[str, Any]) -> Dict[str, Any]:
        return content

    def update_content(self, action: EventAction, job_name: str, job_data: Dict[str, Any], yaml_filename: str):
        content = self.load(yaml_filename)
        prom_config = self.get_prometheus_config(content)
        scrape_configs = prom_config.get("scrape_configs", [])

        existing_job_index = -1
        for i, job in enumerate(scrape_configs):
            if job.get("job_name") == job_name:
                existing_job_index = i
                break
        
        if action == EventAction.CREATE:
            if existing_job_index != -1:
                scrape_configs[existing_job_index] = job_data
            else:
                scrape_configs.append(job_data)
        elif action == EventAction.UPDATE:
            if existing_job_index != -1:
                scrape_configs[existing_job_index] = job_data
            else:
                scrape_configs.append(job_data)
        elif action == EventAction.DELETE:
            if existing_job_index != -1:
                del scrape_configs[existing_job_index]
            else:
                self.logger.warning(f"Job {job_name} not found")
                return
        
        prom_config["scrape_configs"] = scrape_configs
        self.save(content, yaml_filename, prom_config)
        self.reload()
        
        