import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from .model_manager import (
    ModelManager,
    ModelInfo,
)  # Replace with the actual module name
import os

hotkey = "test_hotkey"
repo_id = "test_repo_id"
filename = "test_filename"


@pytest.fixture
def model_manager() -> ModelManager:
    config_obj = SimpleNamespace(**{"model_dir": "/tmp/models"})
    return ModelManager(config=config_obj)


def test_add_model(model_manager: ModelManager) -> None:
    model_manager.add_model(hotkey, repo_id, filename)

    assert hotkey in model_manager.get_state()
    assert model_manager.get_state()[hotkey]["hf_repo_id"] == repo_id
    assert model_manager.get_state()[hotkey]["hf_model_filename"] == filename


def test_delete_model(model_manager: ModelManager) -> None:
    model_manager.add_model(hotkey, repo_id, filename)
    model_manager.delete_model(hotkey)

    assert hotkey not in model_manager.get_state()


def test_sync_hotkeys(model_manager: ModelManager):
    model_manager.add_model(hotkey, repo_id, filename)
    model_manager.sync_hotkeys([])

    assert hotkey not in model_manager.get_state()


@pytest.mark.skip(
    reason="we don't want to test every time with downloading data from huggingface"
)
def test_real_downloading(model_manager: ModelManager) -> None:
    model_manager.add_model(
        "example", "vidhiparikh/House-Price-Estimator", "model_custom.pkcls"
    )
    model_manager.download_miner_model("example")
    model_path = model_manager.hotkey_store["example"].file_path

    assert os.path.exists(model_path)

    # delete the file
    model_manager.delete_model("example")

    # assert the file is deleted
    assert not os.path.exists(model_path)
