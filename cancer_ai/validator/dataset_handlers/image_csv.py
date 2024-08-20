from .base_handler import BaseDatasetHandler
from PIL import Image
from typing import List, Tuple
from dataclasses import dataclass
import csv
import aiofiles
from pathlib import Path


@dataclass
class ImageEntry:
    filepath: str
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

    def __init__(self, config, path: str) -> None:
        self.config = config
        self.label_path = path
        self.metadata_columns = ["filepath", "is_melanoma"]

    async def sync_training_data(self):
        self.entries: List[ImageEntry] = []
        # go over csv file
        async with aiofiles.open(self.label_path, "r") as f:
            # "path" "is_melanoma" columns
            reader = csv.reader(await f.readlines())
            next(reader)  # skip first line
            for row in reader:
                self.entries.append(ImageEntry(row[0], row[1]))

    async def get_training_data(self) -> Tuple[List, List]:
        await self.sync_training_data()
        print(self.entries)
        pred_x = [Image.open(f"{Path(self.label_path).parent}/{entry.filepath}") for entry in self.entries]
        pred_y = [entry.is_melanoma for entry in self.entries]
        await self.process_training_data()
        return pred_x, pred_y
