import os
import shutil
from pathlib import Path
from .manager import SerializableManager
from huggingface_hub import HfApi

from typing import List, Tuple
from async_unzip.unzipper import unzip
from io import BytesIO
from .utils import run_command
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
        self.local_compressed_path = ""
        self.local_extracted_dir = Path(
            self.config.models.dataset_dir, self.competition_id
        )
        self.data: Tuple[List, List] = ()

    def get_state(self) -> dict:
        return {}

    def set_state(self, state: dict):
        return {}

    def download_dataset(self):
        if not os.path.exists(self.local_extracted_dir):
            os.makedirs(self.local_extracted_dir)

        self.local_compressed_path = self.hf_api.hf_hub_download(
            self.dataset_hf_id,
            self.file_hf_id,
            cache_dir=Path(self.config.models.dataset_dir),
            repo_type="dataset",
        )

    def delete_dataset(self):
        shutil.rmtree(self.local_compressed_path)

    async def unzip_dataset(self):
        print("Unzipping dataset", self.local_compressed_path)
        os.system(f"rm -R {self.local_extracted_dir}")
        await run_command(
            f"unzip {self.local_compressed_path} -d {self.local_extracted_dir}"
        )
        print("Dataset unzipped")

    def set_dataset_handler(self):
        if not self.local_compressed_path:
            raise Exception("Dataset not downloaded")
        # is csv in directory
        if os.path.exists(Path(self.local_extracted_dir, "labels.csv")):
            self.handler = DatasetImagesCSV(
                self.config, Path(self.local_extracted_dir, "labels.csv")
            )
        else:
            print("Files in dataset: ", os.listdir(self.local_extracted_dir))
            raise NotImplementedError("Dataset handler not implemented")

    async def prepare_dataset(self):
        self.download_dataset()
        await self.unzip_dataset()
        self.set_dataset_handler()
        self.data = await self.handler.get_training_data()

    async def get_data(self) -> Tuple[List, List]:
        if not self.data:
            raise Exception("Dataset not initalized ")
        return self.data
