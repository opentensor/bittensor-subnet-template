import os
from zipfile import ZipFile
import shutil
from pathlib import Path
from .manager import SerializableManager
from huggingface_hub import HfApi

from typing import List, Tuple
import aiofiles
import aiozip
from io import BytesIO

from .dataset_handlers.image_csv import DatasetImagesCSV


class DatasetManager(SerializableManager):
    def __init__(
        self, config, competition_id: str, dataset_hf_id: str, file_hf_id: str
    ) -> None:
        self.config = config
        self.competition_id = competition_id
        self.dataset_hf_id = dataset_hf_id
        self.file_hf_id = file_hf_id
        self.hf_api = HfApi()
        self.path = ""
        self.data = None

    def get_state(self) -> dict:
        return {}

    def set_state(self, state: dict):
        return {}

    def download_dataset(self):
        if not os.path.exists(
            Path(self.config.models.dataset_dir, self.competition_id)
        ):
            os.makedirs(Path(self.config.models.dataset_dir, self.competition_id))

        self.path = self.hf_api.hf_hub_download(
            self.dataset_hf_id,
            self.file_hf_id,
            cache_dir=Path(self.config.models.dataset_dir, self.competition_id),
        )

    def delete_dataset(self):
        shutil.rmtree(self.path)

    async def unzip_dataset(self):
        async with aiofiles.open(self.path, "rb") as f:
            data = await f.read()
        async with aiofiles.open(self.path, "wb") as f:
            async with aiozip.AIOZipFile(BytesIO(data)) as z:
                await z.extractall(path=Path(self.path).parent)

    def set_dataset_handler(self):
        if not self.path:
            raise Exception("Dataset not downloaded")
        # is csv in directory
        if os.path.exists(Path(self.path, "labels.csv")):
            self.handler = DatasetImagesCSV(self.config, Path(self.path, "labels.csv"))
        else:
            print("Files in dataset: ", os.listdir(self.path))
            raise NotImplementedError("Dataset handler not implemented")

    async def prepare_dataset(self):
        await self.download_dataset()
        await self.unzip_dataset()
        self.set_dataset_handler()

    
    async def get_data(self) -> Tuple[List, List]:
        if not self.data:
            await self.prepare_dataset()
            self.data = await self.handler.get_training_data()
        return self.data
