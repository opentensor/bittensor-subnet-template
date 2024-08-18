from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from datetime import time


class CompetitionManager(SerializableManager):
    """
    CompetitionManager is responsible for managing a competition.

    It handles the scoring, model management and synchronization with the chain.
    """

    def __init__(
        self,
        config,
        competition_id: str,
        category: str,
        evaluation_time: list[time],
        dataset_hf_id: str,
        file_hf_id: str,
    ) -> None:
        """
        Initializes a CompetitionManager instance.

        Args:
        config (dict): Config dictionary.
        competition_id (str): Unique identifier for the competition.
        category (str): Category of the competition.
        evaluation_time (list[time]): List of times of a day at which the competition will be evaluated.

        Note: Times are in UTC time.
        """
        self.config = config
        self.competition_id = competition_id
        self.category = category
        self.model_manager = ModelManager(config)
        self.evaluation_time = evaluation_time
        self.dataset_manager: DatasetManager = DatasetManager(
            config, competition_id, dataset_hf_id, file_hf_id
        )

    def get_state(self):
        return {
            "competition_id": self.competition_id,
            "model_manager": self.model_manager.get_state(),
            "category": self.category,
            "evaluation_time": self.evaluation_time,
        }

    def set_state(self, state: dict):
        self.competition_id = state["competition_id"]
        self.model_manager.set_state(state["model_manager"])
        self.category = state["category"]
        self.evaluation_time = state["evaluation_time"]

    async def get_miner_model(self, hotkey):
        # test data
        return ModelInfo("vidhiparikh/House-Price-Estimator", "model_custom.pkcls")

    async def init_evaluation(self):
        for hotkey in self.model_manager.hotkey_store:
            self.model_manager.hotkey_store[hotkey] = await self.get_miner_model(hotkey)
            await self.model_manager.download_miner_model(hotkey)

        # log event

    async def evaluate(self):
        self.init_evaluation()
        self.dataset
        for hotkey in self.model_manager.hotkey_store:
            print("Evaluating hotkey: ", hotkey)
