import time
from typing import List

import bittensor as bt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    roc_curve,
    auc,
)
import wandb

from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager

from .competition_handlers.melanoma_handler import MelanomaCompetitionHandler
from .competition_handlers.base_handler import ModelEvaluationResult

from cancer_ai.chain_models_store import ChainModelMetadataStore, ChainMinerModel
from dotenv import load_dotenv

load_dotenv()

COMPETITION_HANDLER_MAPPING = {
    "melanoma-1": MelanomaCompetitionHandler,
    "melanoma-testnet": MelanomaCompetitionHandler,
    "melanoma-7": MelanomaCompetitionHandler,
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
        hotkeys: list[str],
        competition_id: str,
        category: str,
        dataset_hf_repo: str,
        dataset_hf_id: str,
        dataset_hf_repo_type: str,
        test_mode: bool = False,
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
        self.model_manager = ModelManager(self.config)
        self.dataset_manager = DatasetManager(
            self.config,
            competition_id,
            dataset_hf_repo,
            dataset_hf_id,
            dataset_hf_repo_type,
        )
        self.chain_model_metadata_store = ChainModelMetadataStore(
            self.config.subtensor.network, self.config.netuid
        )

        self.hotkeys = hotkeys
        self.chain_miner_models = {}
        self.test_mode = test_mode

    def __repr__(self) -> str:
        return f"CompetitionManager<{self.competition_id}>"

    def log_results_to_wandb(
        self, hotkey: str, evaluation_result: ModelEvaluationResult
    ) -> None:
        wandb.init(reinit=True, project=self.competition_id, group="model_evaluation")
        wandb.log(
            {
                "hotkey": hotkey,
                "tested_entries": evaluation_result.tested_entries,
                "accuracy": evaluation_result.accuracy,
                "precision": evaluation_result.precision,
                "recall": evaluation_result.recall,
                "confusion_matrix": evaluation_result.confusion_matrix.tolist(),
                "roc_curve": {
                    "fpr": evaluation_result.fpr.tolist(),
                    "tpr": evaluation_result.tpr.tolist(),
                },
                "roc_auc": evaluation_result.roc_auc,
            }
        )

        wandb.finish()
        bt.logging.info("Results: ", evaluation_result)

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
        if chain_miner_model.competition_id != self.competition_id:
            raise ValueError(
                f"Chain miner model {chain_miner_model.to_compressed_str()} does not belong to this competition"
            )
        model_info = ModelInfo(
            hf_repo_id=chain_miner_model.hf_repo_id,
            hf_model_filename=chain_miner_model.hf_filename,
            hf_code_filename=chain_miner_model.hf_code_filename,
            hf_repo_type=chain_miner_model.hf_repo_type,
            competition_id=chain_miner_model.competition_id,
        )
        return model_info

    async def sync_chain_miners_test(self):
        """Get registered mineres from testnet subnet 163"""

        hotkeys_with_models = {
            "5Fo2fenxPY1D7hgTHc88g1zrX2ZX17g8DvE5KnazueYefjN5": ModelInfo(
                hf_repo_id="safescanai/test_dataset",
                hf_model_filename="model_dynamic.onnx",
                hf_repo_type="dataset",
            ),
            "5DZZnwU2LapwmZfYL9AEAWpUR6FoFvqHnzQ5F71Mhwotxujq": ModelInfo(
                hf_repo_id="safescanai/test_dataset",
                hf_model_filename="best_model.onnx",
                hf_repo_type="dataset",
            ),
        }
        self.model_manager.hotkey_store = hotkeys_with_models

    async def sync_chain_miners(self):
        """
        Updates hotkeys and downloads information of models from the chain
        """
        bt.logging.info("Synchronizing miners from the chain")
        bt.logging.info(f"Amount of hotkeys: {len(self.hotkeys)}")
        for hotkey in self.hotkeys:
            hotkey_metadata = (
                await self.chain_model_metadata_store.retrieve_model_metadata(hotkey)
            )
            if not hotkey_metadata:
                bt.logging.warning(
                    f"Cannot get miner model for hotkey {hotkey} from the chain, skipping"
                )
                continue
            try:
                miner_model = await self.get_miner_model(hotkey)
                self.chain_miner_models[hotkey] = hotkey_metadata
                self.model_manager.hotkey_store[hotkey] = miner_model
            except ValueError:
                bt.logging.error(
                    f"Miner {hotkey} with data  {hotkey_metadata.to_compressed_str()} does not belong to this competition, skipping"
                )
        bt.logging.info(
            f"Amount of chain miners with models: {len(self.chain_miner_models)}"
        )

    async def evaluate(self) -> str:
        """Returns hotkey and competition id of winning model miner"""
        await self.dataset_manager.prepare_dataset()
        X_test, y_test = await self.dataset_manager.get_data()

        competition_handler = COMPETITION_HANDLER_MAPPING[self.competition_id](
            X_test=X_test, y_test=y_test
        )
        # TODO get hotkeys
        if self.test_mode:
            await self.sync_chain_miners_test()
        else:
            await self.sync_chain_miners()

        y_test = competition_handler.prepare_y_pred(y_test)
        # bt.logging.info("Ground truth: ", y_test)
        for hotkey in self.model_manager.hotkey_store:
            bt.logging.info("Evaluating hotkey: ", hotkey)
            await self.model_manager.download_miner_model(hotkey)

            model_manager = ModelRunManager(
                self.config, self.model_manager.hotkey_store[hotkey]
            )
            start_time = time.time()
            y_pred = await model_manager.run(X_test)
            run_time_s = time.time() - start_time
            # bt.logging.info("Model prediction ", y_pred)

            model_result = competition_handler.get_model_result(
                y_test, y_pred, run_time_s
            )
            self.results.append((hotkey, model_result))
            self.log_results_to_wandb(hotkey, model_result)

        winning_hotkey = sorted(
            self.results, key=lambda x: x[1].accuracy, reverse=True
        )[0][0]
        return winning_hotkey
