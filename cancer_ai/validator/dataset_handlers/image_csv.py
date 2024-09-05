from .base_handler import BaseDatasetHandler
from PIL import Image
from typing import List, Tuple
from dataclasses import dataclass
import csv
import aiofiles
from pathlib import Path

from ..utils import log_time


@dataclass
class ImageEntry:
    relative_path: str
    is_melanoma: bool


class DatasetImagesCSV(BaseDatasetHandler):
    """
    DatasetImagesCSV is responsible for handling the CSV dataset where directory structure looks as follows:

    ├── images
    │   ├── image_1.jpg
    │   ├── image_2.jpg
    │   └── ...
    ├── labels.csv
    """

    def __init__(self, config, dataset_path, label_path: str) -> None:
        self.config = config
        self.dataset_path = dataset_path
        self.label_path = label_path
        self.metadata_columns = ["filepath", "is_melanoma"]

    @log_time
    async def sync_training_data(self):
        self.entries: List[ImageEntry] = []
        # go over csv file
        async with aiofiles.open(self.label_path, "r") as f:
            # "path" "is_melanoma" columns
            reader = csv.reader(await f.readlines())
            next(reader)  # skip first line
            for row in reader:
                self.entries.append(ImageEntry(row[0], row[1]))

    @log_time
    async def get_training_data(self) -> Tuple[List, List]:
        """
        Get the training data.

        This method is responsible for loading the training data and returning a tuple containing two lists: the first list contains paths to the images and the second list contains the labels.
        """
        await self.sync_training_data()
        pred_x = [
            Path(self.dataset_path, entry.relative_path).resolve()
            for entry in self.entries
        ]
        pred_y = [entry.is_melanoma for entry in self.entries]
        await self.process_training_data()
        return pred_x, pred_y
