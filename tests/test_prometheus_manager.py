import pytest
from unittest.mock import MagicMock, patch
from prometheus_manager.git_prometheus_manager import GitPrometheusManager
from prometheus_manager.prometheus_manager import PrometheusManager
from enums.event_actions import EventAction


@pytest.fixture
def manager():
    with patch("git.Repo") as mock_repo:
        # Mocking file operations to avoid real IO
        with patch("os.path.exists", return_value=True):
            manager = GitPrometheusManager("http://url", "/tmp", "main")
            manager.yaml = MagicMock()
            manager.load = MagicMock(return_value={"scrape_configs": []})
            manager.save = MagicMock()
            manager.reload = MagicMock()
            return manager


def test_update_content_create(manager):
    job_data = {"job_name": "new_job", "other": "data"}
    manager.update_content(EventAction.CREATE, "new_job", job_data, "file.yaml")

    # Check that save was called with the new job appended
    manager.save.assert_called_once()
    saved_content = manager.save.call_args[0][0]  # First arg
    # Note: Since we mocked load() to return same dict, we need to inspect what was passed to save
    # Actually, the logic modifies the list in place from the return of load()
    # Let's inspect the call arguments to save
    # But wait, manager.load return value is a mock? No, we set return_value to a dict

    # Re-verify logic:
    # content = self.load() -> dict
    # prom_config = ... (same dict)
    # scrape_configs = prom_config.get(...)
    # modify scrape_configs
    # self.save(content, ...)

    # So if we verify arguments to save, we can see if list has the item.
    assert len(manager.save.call_args[0][0]["scrape_configs"]) == 1
    assert manager.save.call_args[0][0]["scrape_configs"][0]["job_name"] == "new_job"


def test_update_content_update_existing(manager):
    # Setup existing state
    manager.load.return_value = {"scrape_configs": [{"job_name": "existing", "val": 1}]}

    new_data = {"job_name": "existing", "val": 2}
    manager.update_content(EventAction.UPDATE, "existing", new_data, "file.yaml")

    saved_configs = manager.save.call_args[0][0]["scrape_configs"]
    assert len(saved_configs) == 1
    assert saved_configs[0]["val"] == 2


def test_update_content_delete(manager):
    manager.load.return_value = {"scrape_configs": [{"job_name": "to_delete"}]}

    manager.update_content(EventAction.DELETE, "to_delete", {}, "file.yaml")

    saved_configs = manager.save.call_args[0][0]["scrape_configs"]
    assert len(saved_configs) == 0


def test_git_operations():
    # Test that init pulls if exists
    with patch("os.path.exists", return_value=True):
        with patch("git.Repo") as mock_repo:
            GitPrometheusManager("url", "path", "branch")
            mock_repo.assert_called_with("path")
            mock_repo.return_value.remotes.origin.pull.assert_called()


def test_rollback():
    with patch("os.path.exists", return_value=True):
        with patch("git.Repo") as mock_repo:
            mgr = GitPrometheusManager("url", "path", "branch")
            mgr.rollback()
            mgr.repo.git.reset.assert_called_with("--hard")
