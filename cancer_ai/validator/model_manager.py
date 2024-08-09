from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime
from time import sleep
import os
from huggingface_hub import HfApi

from .manager import SerializableManager


@dataclass
class ModelInfo:
    repo_id: str
    filename: str
    file_path: str | None = None


class ModelManager(SerializableManager):
    def __init__(self, config) -> None:
        self.config = config
        if "model_dir" not in self.config:
            self.config["model_dir"] = "./models"
        # create model_dir if it doesn't exist
        if not os.path.exists(self.config["model_dir"]):
            os.makedirs(self.config["model_dir"])
        self.api = HfApi()
        self.hotkey_store = {}  # Now a dictionary mapping hotkeys to ModelInfo objects

    def get_state(self):
        return {k: asdict(v) for k, v in self.hotkey_store.items() if is_dataclass(v)}

    def set_state(self, hotkey_models: dict):
        self.hotkey_store = {k: ModelInfo(**v) for k, v in hotkey_models.items()}

    def sync_hotkeys(self, hotkeys: list):
        hotkey_copy = list(self.hotkey_store.keys())
        for hotkey in hotkey_copy:
            if hotkey not in hotkeys:
                self.delete_model(hotkey)

    def download_miner_model(self, hotkey) -> None:
        """Downloads the newest model from Hugging Face and saves it to disk.
        Returns:
            str: path to the downloaded model
        """
        model_info = self.hotkey_store[hotkey]
        model_path = self.api.hf_hub_download(
            model_info.repo_id,
            model_info.filename,
            cache_dir=self.config["model_dir"],
            repo_type="space",
        )
        model_info.file_path = model_path

    def add_model(self, hotkey, repo_id, filename) -> None:
        """Saves locally information about a new model."""
        self.hotkey_store[hotkey] = ModelInfo(repo_id, filename)

    def delete_model(self, hotkey):
        """Deletes locally information about a model and the corresponding file on disk."""

        print("Deleting model: ", hotkey)
        if hotkey in self.hotkey_store and self.hotkey_store[hotkey].file_path:
            os.remove(self.hotkey_store[hotkey].file_path)
        self.hotkey_store[hotkey] = None
