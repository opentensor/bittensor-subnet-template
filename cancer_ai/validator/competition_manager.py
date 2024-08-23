import time
import random
from typing import List

import bittensor as bt

from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager

from  .competition_handlers.melanoma_handler import MelanomaCompetitionHandler



COMPETITION_HANDLER_MAPPING = {
    "melaona-1": MelanomaCompetitionHandler,
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
        evaluation_times: list[str],
        dataset_hf_id: str,
        file_hf_id: str,
    ) -> None:
        """
        Initializes a CompetitionManager instance.

        Args:
        config (dict): Config dictionary.
        competition_id (str): Unique identifier for the competition.
        category (str): Category of the competition.
        evaluation_time (list[str]): List of times of a day at which the competition will be evaluated in XX:XX format.

        Note: Times are in UTC time.
        """
        bt.logging.info(f"Initializing Competition: {competition_id}")
        self.config = config
        self.competition_id = competition_id
        self.category = category
        self.model_manager = ModelManager(config)

        # self.evaluation_time = [
        #     time(hour_min.split(":")[0], hour_min.split(":")[1])
        #     for hour_min in evaluation_times
        # ]
        self.dataset_manager = DatasetManager(
            config, competition_id, dataset_hf_id, file_hf_id
        )
        # self.model_evaluator =
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
        # TODO get real data
        return ModelInfo("safescanai/test_dataset", "melanoma.keras")

    async def init_evaluation(self):
        # TODO get models from chain
        miner_models = [
            # {
            #     "hotkey": "obcy ludzie_2",
            #     "hf_id": "safescanai/test_dataset",
            #     "file_hf_id": "model_dynamic.onnx",
            # },
            {
                "hotkey": "obcy ludzie",
                "hf_id": "safescanai/test_dataset",
                "file_hf_id": "model_dynamic.onnx",
            },
        ]
        bt.logging.info(
            f"Populating model manager with miner models. Got {len(miner_models)} models"
        )
        for miner_info in miner_models:
            self.model_manager.add_model(
                miner_info["hotkey"], miner_info["hf_id"], miner_info["file_hf_id"]
            )
        bt.logging.info("Initializing dataset")
        await self.dataset_manager.prepare_dataset()

        # log event

    async def evaluate(self):
        await self.init_evaluation()
        path_X_test, y_test = await self.dataset_manager.get_data()
        
        competition_handler = COMPETITION_HANDLER_MAPPING[self.competition_id](
            path_X_test=path_X_test, y_test=y_test
        )

        X_test, y_test = competition_handler.preprocess_data()

        for hotkey in self.model_manager.hotkey_store:
            bt.logging.info("Evaluating hotkey: ", hotkey)
            await self.model_manager.download_miner_model(hotkey)

            model_manager = ModelRunManager(
                self.config, self.model_manager.hotkey_store[hotkey]
            )
            start_time = time.time()
            y_pred = model_manager.run(X_test)
            run_time_s = time.time() - start_time
            print("Model prediction ", y_pred)
            print("Ground truth: ", y_test)
            
            model_result = competition_handler.get_model_result(y_test, y_pred, run_time_s)
            self.results.append((hotkey, model_result))

        return self.results
