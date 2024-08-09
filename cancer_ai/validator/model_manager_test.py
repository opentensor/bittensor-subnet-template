import pytest
from unittest.mock import patch, MagicMock
from .model_manager import ModelManager  # Replace with the actual module name

hotkey = "test_hotkey"
repo_id = "test_repo_id"
filename = "test_filename"


@pytest.fixture
def model_manager():
    config = {}
    return ModelManager(config)


def test_add_model(model_manager: ModelManager):
    model_manager.add_model(hotkey, repo_id, filename)

    assert hotkey in model_manager.get_model_state()
    assert model_manager.get_model_state()[hotkey]["repo_id"] == repo_id
    assert model_manager.get_model_state()[hotkey]["filename"] == filename


def test_delete_model(model_manager: ModelManager):
    model_manager.add_model(hotkey, repo_id, filename)
    model_manager.delete_model(hotkey)

    assert hotkey not in model_manager.get_model_state()


def test_sync_hotkeys(model_manager: ModelManager):
    model_manager.add_model(hotkey, repo_id, filename)

    model_manager.sync_hotkeys([])

    assert hotkey not in model_manager.get_model_state()


def test_load_save_model_state(model_manager: ModelManager):
    hotkey_models = {
        "test_hotkey_1": {"repo_id": "repo_1", "filename": "file_1"},
        "test_hotkey_2": {"repo_id": "repo_2", "filename": "file_2"},
    }

    model_manager.initialize_model_state(hotkey_models)

    assert model_manager.get_model_state() == hotkey_models
