from datetime import time
import random
from typing import List

import bittensor as bt

from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager


COMPETITION_MAPPING = {
    "melaona-1": "melanoma",
}


class ImagePredictionCompetition:
    def score_model(
        self, model_info: ModelInfo, pred_y: List, model_pred_y: List
    ) -> float:
        pass


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
        dataset_hf_id: str,
        file_hf_id: str,
    ) -> None:
        """
        Responsible for managing a competition.

        Args:
        config (dict): Config dictionary.
        competition_id (str): Unique identifier for the competition.
        category (str): Category of the competition.
        """
        bt.logging.info(f"Initializing Competition: {competition_id}")
        self.config = config
        self.competition_id = competition_id
        self.category = category
        self.results = []
        self.model_manager = ModelManager(config)
        self.dataset_manager = DatasetManager(
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

    async def get_miner_model(self, hotkey):
        # TODO get real data
        return ModelInfo("safescanai/test_dataset", "simple_cnn_model.onnx")

    async def init_evaluation(self):
        # get models from chain
        hotkeys = [
            "example_hotkey",
        ]
        for hotkey in hotkeys:
            self.model_manager.hotkey_store[hotkey] = await self.get_miner_model(hotkey)

        await self.dataset_manager.prepare_dataset()

        # log event

    async def evaluate(self):
        await self.init_evaluation()
        pred_x, pred_y = await self.dataset_manager.get_data()
        for hotkey in self.model_manager.hotkey_store:
            bt.logging.info("Evaluating hotkey: ", hotkey)
            await self.model_manager.download_miner_model(hotkey)

            model_manager = ModelRunManager(
                self.config, self.model_manager.hotkey_store[hotkey]
            )
            model_pred_y = await model_manager.run(pred_x)
            # print "make stats and send to wandb"
            score = random.randint(0, 100)
            bt.logging.info(f"Hotkey {hotkey} model score: {score}")
            self.results.append((hotkey, score))

        # sort by score
        self.results.sort(key=lambda x: x[1], reverse=True)
        return self.results
