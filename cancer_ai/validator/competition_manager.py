from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager
from datetime import time
import random

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
        self.results = []

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
            
        self.dataset_manager.prepare_dataset()
        
        # log event

    async def evaluate(self):
        self.init_evaluation()
        pred_x, pred_y = self.dataset_manager.get_data()
        for hotkey in self.model_manager.hotkey_store:
            print("Evaluating hotkey: ", hotkey)
            await self.model_manager.download_miner_model(hotkey)
            pred_y = ModelRunManager(self.config, self.model_manager.hotkey_store[hotkey]).run(pred_x)
            # print "make stats and send to wandb"
            score = random.randint(0, 100)
            self.results.append((hotkey, score))

        # sort by score 
        self.results.sort(key=lambda x: x[1], reverse=True)
        return self.results


