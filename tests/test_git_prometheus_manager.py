import pytest
from unittest.mock import MagicMock, patch, mock_open
from prometheus_manager.git_prometheus_manager import GitPrometheusManager
from config.constants import PROD_ENV


@pytest.fixture
def mock_git_repo():
    with patch("git.Repo") as mock:
        yield mock


@pytest.fixture
def mock_yaml():
    with patch("ruamel.yaml.YAML") as mock:
        yield mock


@pytest.fixture
def manager(mock_git_repo, mock_yaml):
    with patch("os.path.exists", return_value=False):  # Force clone
        return GitPrometheusManager("http://repo.git", "/tmp/local", "main")


def test_init_clone(mock_git_repo):
    with patch("os.path.exists", return_value=False):
        GitPrometheusManager("repo", "path", "branch")
        mock_git_repo.clone_from.assert_called_once_with(
            "repo", "path", branch="branch"
        )


def test_init_existing(mock_git_repo):
    with patch("os.path.exists", return_value=True):
        GitPrometheusManager("repo", "path", "branch")
        mock_git_repo.assert_called_with("path")
        # Should pull
        mock_git_repo.return_value.remotes.origin.pull.assert_called()


def test_load_success(manager):
    # Mock pull
    manager.repo = MagicMock()

    with (
        patch("builtins.open", mock_open(read_data="key: value")),
        patch("os.path.exists", return_value=True),
    ):
        manager.yaml = MagicMock()
        manager.yaml.load.return_value = {"key": "value"}

        data = manager.load("file.yaml")

        assert data == {"key": "value"}
        manager.repo.remotes.origin.pull.assert_called_with("main")


def test_load_not_found(manager):
    manager.repo = MagicMock()
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            manager.load("missing.yaml")


def test_save_success_prod(manager):
    manager.repo = MagicMock()
    manager.repo.is_dirty.return_value = True

    # Mock GENERAL_CONFIG to be PROD
    with patch(
        "prometheus_manager.git_prometheus_manager.GENERAL_CONFIG", {"env": PROD_ENV}
    ):
        with patch("builtins.open", mock_open()) as mocked_file:
            manager.save({"data": 1}, "file.yaml", {})

            mocked_file.assert_called()
            # Verify git operations
            manager.repo.index.add.assert_called()
            manager.repo.index.commit.assert_called()
            manager.repo.remotes.origin.push.assert_called_with("main")


def test_save_no_changes(manager):
    manager.repo = MagicMock()
    manager.repo.is_dirty.return_value = False

    with patch(
        "prometheus_manager.git_prometheus_manager.GENERAL_CONFIG", {"env": PROD_ENV}
    ):
        with patch("builtins.open", mock_open()):
            manager.save({"data": 1}, "file.yaml", {})

            manager.repo.remotes.origin.push.assert_not_called()


def test_rollback(manager):
    manager.repo = MagicMock()
    manager.rollback()
    manager.repo.git.reset.assert_called_once_with("--hard")
