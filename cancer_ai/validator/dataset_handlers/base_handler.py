from typing import List, Tuple
from abc import abstractmethod


class BaseDatasetHandler:
    """
    Base class for handling different dataset types.

    This class initializes the config and path attributes.

    Args:
        config (dict): Configuration dictionary.
        path (str): Path to the dataset.

    Attributes:
        config (dict): Configuration dictionary.
        path (str): Path to the dataset.

    """

    def __init__(self, config, path) -> None:
        """
        Initializes the BaseDatasetHandler object.

        Args:
            config (dict): Configuration dictionary.
            path (str): Path to the dataset.

        """
        # Initialize the config and path attributes
        self.config = config  # Configuration dictionary
        self.path = path  # Path to the dataset
        self.entries = []

    @abstractmethod
    async def get_training_data(self) -> Tuple[List, List]:
        """
        Abstract method to get the training data.

        This method is responsible for loading the training data and returning it as a tuple of two lists: the first list contains the input data and the second list contains the labels.

        Returns:
            Tuple[List, List]: A tuple containing two lists: the first list contains the input data and the second list contains the labels.
        """

    @abstractmethod
    async def sync_training_data(self):
        """
        Abstract method to synchronize the training data.

        This method is responsible for reading the training data from the dataset and storing it in the self.entries attribute.
        """

    async def process_training_data(self):
        """
        Process the training data.

        This method is responsible for preprocessing the training data and returning it as a tuple of two lists: the first list contains the input data and the second list contains the labels.

        Returns:
            Tuple[List, List]: A tuple containing two lists: the first list contains the input data and the second list contains the labels.
        """
