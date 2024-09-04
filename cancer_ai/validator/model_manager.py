from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime
from time import sleep
import os
import bittensor as bt
from huggingface_hub import HfApi

from .manager import SerializableManager


@dataclass
class ModelInfo:
    hf_repo_id: str | None = None
    hf_model_filename: str | None = None
    hf_code_filename: str | None = None
    hf_repo_type: str | None = None

    competition_id: str | None = None
    file_path: str | None = None
    model_type: str | None = None


class ModelManager(SerializableManager):
    def __init__(self, config) -> None:
        self.config = config

        if not os.path.exists(self.config.models.model_dir):
            os.makedirs(self.config.models.model_dir)
        self.api = HfApi()
        self.hotkey_store = {}

    def get_state(self):
        return {k: asdict(v) for k, v in self.hotkey_store.items() if is_dataclass(v)}

    def set_state(self, hotkey_models: dict):
        self.hotkey_store = {k: ModelInfo(**v) for k, v in hotkey_models.items()}

    def sync_hotkeys(self, hotkeys: list):
        hotkey_copy = list(self.hotkey_store.keys())
        for hotkey in hotkey_copy:
            if hotkey not in hotkeys:
                self.delete_model(hotkey)

    async def download_miner_model(self, hotkey) -> None:
        """Downloads the newest model from Hugging Face and saves it to disk.
        Returns:
            str: path to the downloaded model
        """
        model_info = self.hotkey_store[hotkey]
        model_info.file_path = self.api.hf_hub_download(
            model_info.hf_repo_id,
            model_info.hf_model_filename,
            cache_dir=self.config.models.model_dir,
            repo_type=model_info.hf_repo_type,
            token=self.config.hf_token if hasattr(self.config, "hf_token") else None,
        )

    def add_model(
        self,
        hotkey,
        hf_repo_id,
        hf_model_filename,
        hf_code_filename=None,
        hf_repo_type=None,
    ) -> None:
        """Saves locally information about a new model."""
        self.hotkey_store[hotkey] = ModelInfo(
            hf_repo_id, hf_model_filename, hf_code_filename, hf_repo_type
        )

    def delete_model(self, hotkey) -> None:
        """Deletes locally information about a model and the corresponding file on disk."""

        bt.logging.info(f"Deleting model: {hotkey}")
        if hotkey in self.hotkey_store and self.hotkey_store[hotkey].file_path:
            os.remove(self.hotkey_store[hotkey].file_path)
        self.hotkey_store[hotkey] = None
