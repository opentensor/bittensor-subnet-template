import os
import shutil
from pathlib import Path
from typing import List, Tuple

from huggingface_hub import HfApi
import bittensor as bt

from .manager import SerializableManager
from .utils import run_command
from .dataset_handlers.image_csv import DatasetImagesCSV


class DatasetManagerException(Exception):
    pass

class DatasetManager(SerializableManager):
    def __init__(
        self, config, competition_id: str, dataset_hf_id: str, file_hf_id: str
    ) -> None:
        """
        Initializes a new instance of the DatasetManager class.
        
        Args:
            config: The configuration object.
            competition_id (str): The ID of the competition.
            dataset_hf_id (str): The Hugging Face ID of the dataset.
            file_hf_id (str): The Hugging Face ID of the file.
        
        Returns:
            None
        """
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
        self.handler = None

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

    def delete_dataset(self) -> None:
        """Delete dataset from disk"""
        shutil.rmtree(self.local_compressed_path)

    async def unzip_dataset(self) -> None:
        """Unzip dataset"""
        print("Unzipping dataset", self.local_compressed_path)
        os.system(f"rm -R {self.local_extracted_dir}")
        print(f"unzip {self.local_compressed_path} -d {self.local_extracted_dir}")
        out, err = await run_command(
            f"unzip {self.local_compressed_path} -d {self.local_extracted_dir}"
        )
        print(err)
        print("Dataset unzipped")

    def set_dataset_handler(self) -> None:
        """Detect dataset type and set handler"""
        if not self.local_compressed_path:
            raise DatasetManagerException("Dataset not downloaded")
        # is csv in directory
        if os.path.exists(Path(self.local_extracted_dir, "labels.csv")):
            self.handler = DatasetImagesCSV(
                self.config, Path(self.local_extracted_dir, "labels.csv")
            )
        else:
            #print("Files in dataset: ", os.listdir(self.local_extracted_dir))
            raise NotImplementedError("Dataset handler not implemented")

    async def prepare_dataset(self) -> None:
        """Download dataset, unzip and set dataset handler"""

        bt.logging.info("Downloading dataset")
        self.download_dataset()
        bt.logging.info("Unzipping dataset")
        await self.unzip_dataset()
        bt.logging.info("Setting dataset handler")
        self.set_dataset_handler()
        bt.logging.info("Preprocessing dataset")
        self.data = await self.handler.get_training_data()

    async def get_data(self) -> Tuple[List, List]:
        """Get data from dataset handler"""
        if not self.data:
            raise DatasetManagerException("Dataset not initalized ")
        return self.data
