import time
import random
from typing import List

import bittensor as bt

from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager

from .competition_handlers.melanoma_handler import MelanomaCompetitionHandler

from cancer_ai.chain_models_store import ChainModelMetadataStore, ChainMinerModel


COMPETITION_HANDLER_MAPPING = {
    "melanoma-1": MelanomaCompetitionHandler,
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
        subtensor: bt.Subtensor,
        subnet_uid: str,
        competition_id: str,
        category: str,
        dataset_hf_repo: str,
        dataset_hf_id: str,
        dataset_hf_repo_type: str,
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
            config, competition_id, dataset_hf_repo, dataset_hf_id, dataset_hf_repo_type
        )
        self.chain_model_metadata_store = ChainModelMetadataStore(subtensor, subnet_uid)

        self.hotkeys = []
        self.chain_miner_models = {}

    def get_state(self):
        return {
            "competition_id": self.competition_id,
            "model_manager": self.model_manager.get_state(),
            "category": self.category,
        }

    def set_state(self, state: dict):
        self.competition_id = state["competition_id"]
        self.model_manager.set_state(state["model_manager"])
        self.category = state["category"]

    async def get_miner_model(self, chain_miner_model: ChainMinerModel):
        model_info = ModelInfo(
            hf_repo_id=chain_miner_model.hf_repo_id,
            hf_filename=chain_miner_model.hf_filename,
            hf_repo_type=chain_miner_model.hf_repo_type,
        )
        return model_info

        # return ModelInfo(hf_repo_id="safescanai/test_dataset", hf_filename="simple_cnn_model.onnx", hf_repo_type="dataset")

    async def sync_chain_miners(self, hotkeys: list[str]):
        """
        Updates hotkeys and downloads information of models from the chain
        """
        bt.logging.info("Synchronizing miners from the chain")
        self.hotkeys = hotkeys
        bt.logging.info(f"Amount of hotkeys: {len(hotkeys)}")
        for hotkey in hotkeys:
            hotkey_metadata = (
                await self.chain_model_metadata_store.retrieve_model_metadata(hotkey)
            )
            if hotkey_metadata:
                self.chain_miner_models[hotkey] = hotkey_metadata
                self.model_manager.hotkey_store[hotkey] = await self.get_miner_model(
                    hotkey
                )
        bt.logging.info(
            f"Amount of chain miners with models: {len(self.chain_miner_models)}"
        )

    async def evaluate(self):
        await self.dataset_manager.prepare_dataset()
        X_test, y_test = await self.dataset_manager.get_data()

        competition_handler = COMPETITION_HANDLER_MAPPING[self.competition_id](
            X_test=X_test, y_test=y_test
        )

        X_test, y_test = competition_handler.preprocess_data()

        for hotkey in self.model_manager.hotkey_store:
            bt.logging.info("Evaluating hotkey: ", hotkey)
            await self.model_manager.download_miner_model(hotkey)

            model_manager = ModelRunManager(
                self.config, self.model_manager.hotkey_store[hotkey]
            )
            start_time = time.time()
            y_pred = await model_manager.run(X_test)
            run_time_s = time.time() - start_time
            print("Model prediction ", y_pred)
            print("Ground truth: ", y_test)

            model_result = competition_handler.get_model_result(
                y_test, y_pred, run_time_s
            )
            self.results.append((hotkey, model_result))

        return self.results
