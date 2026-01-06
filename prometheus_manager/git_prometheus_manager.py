import os.path
import git
from config.constants import PROD_ENV
from prometheus_manager.prometheus_manager import PrometheusManager
from typing import Dict, Any
from config import GENERAL_CONFIG

class GitPrometheusManager(PrometheusManager):
    def __init__(self, repo_url: str, local_path: str, branch: str):
        super().__init__()
        self.repo_url = repo_url
        self.local_path = local_path
        self.branch = branch

        self._init_repo()
    
    @staticmethod
    def get_prometheus_config(content: Dict[str, Any]) -> Dict[str, Any]:
        return content
    
    def _init_repo(self):
        os.environ['GIT_SSL_NO_VERIFY'] = "true"

        if not os.path.exists(self.local_path):
            self.repo = git.Repo.clone_from(self.repo_url, self.local_path, branch=self.branch)
        else:
            self.repo = git.Repo(self.local_path)
            self._pull()

    def _pull(self):
        try:
            origin = self.repo.remotes.origin
            origin.pull(self.branch)
        except git.GitError as e:
            self.logger.error(f"Failed to pull from remote: {e}")
            raise e

    def load(self, yaml_filename: str) -> Dict[str, Any]:
        self._pull()
        yaml_path = os.path.join(self.local_path, yaml_filename)

        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")

        with open(yaml_path, 'r') as f:
            return self.yaml.load(f) or {"global": {}, "scrape_configs": []}
    
    def save(self, content: Dict[str, Any], yaml_filename: str, prom_config: Dict[str, Any]) -> None:
        yaml_path = os.path.join(self.local_path, yaml_filename)

        try:
            with open(yaml_path, 'w') as f:
                self.yaml.dump(content, f)

            if GENERAL_CONFIG['env'] == PROD_ENV:
                if self.repo.is_dirty():
                    self.repo.index.add(yaml_path)
                    self.repo.index.commit("Update prometheus.yaml")

                    origin = self.repo.remotes.origin
                    origin.push(self.branch)
                else:
                    self.logger.info("No changes to commit")
        except Exception as e:
            self.logger.error(f"Failed to save YAML file: {e}")
            raise e
    
    def reload(self):
        pass

    def rollback(self):
        try:
            self.repo.git.reset('--hard')
            self.logger.info("Successfully rolled back to last commit")
        except Exception as e:
            self.logger.error(f"Failed to rollback: {e}")
                