import time
from typing import List, Tuple

import bittensor as bt
import wandb
from dotenv import load_dotenv

from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager
from .exceptions import ModelRunException

from .competition_handlers.melanoma_handler import MelanomaCompetitionHandler
from .competition_handlers.base_handler import ModelEvaluationResult
from .tests.mock_data import get_mock_hotkeys_with_models
from cancer_ai.chain_models_store import (
    ChainModelMetadata,
    ChainMinerModel,
    ChainMinerModelStore,
)

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
        subtensor: bt.subtensor,
        hotkeys: list[str],
        validator_hotkey: str,
        chain_miners_store: ChainMinerModelStore,
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
        bt.logging.trace(f"Initializing Competition: {competition_id}")
        self.config = config
        self.subtensor = subtensor
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
        self.chain_model_metadata_store = ChainModelMetadata(
            self.subtensor, self.config.netuid
        )

        self.hotkeys = hotkeys
        self.validator_hotkey = validator_hotkey
        self.chain_miners_store = chain_miners_store
        self.test_mode = test_mode

    def __repr__(self) -> str:
        return f"CompetitionManager<{self.competition_id}>"

    def log_results_to_wandb(
        self, miner_hotkey: str, validator_hotkey: str, evaluation_result: ModelEvaluationResult
    ) -> None:
        wandb.init(project=self.competition_id, group="model_evaluation")
        wandb.log(
            {
                "miner_hotkey": miner_hotkey,
                "validator_hotkey": validator_hotkey,
                "tested_entries": evaluation_result.tested_entries,
                "accuracy": evaluation_result.accuracy,
                "precision": evaluation_result.precision,
                "fbeta": evaluation_result.fbeta,
                "recall": evaluation_result.recall,
                "confusion_matrix": evaluation_result.confusion_matrix,
                "roc_curve": {
                    "fpr": evaluation_result.fpr,
                    "tpr": evaluation_result.tpr,
                },
                "roc_auc": evaluation_result.roc_auc,
                "score": evaluation_result.score,
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

    async def chain_miner_to_model_info(
        self, chain_miner_model: ChainMinerModel
    ) -> ModelInfo | None:
        bt.logging.warning(f"Chain miner model: {chain_miner_model.model_dump()}")
        if chain_miner_model.competition_id != self.competition_id:
            bt.logging.debug(
                f"Chain miner model {chain_miner_model.to_compressed_str()} does not belong to this competition"
            )
            raise ValueError("Chain miner model does not belong to this competition")
        model_info = ModelInfo(
            hf_repo_id=chain_miner_model.hf_repo_id,
            hf_model_filename=chain_miner_model.hf_model_filename,
            hf_code_filename=chain_miner_model.hf_code_filename,
            hf_repo_type=chain_miner_model.hf_repo_type,
            competition_id=chain_miner_model.competition_id,
        )
        return model_info

    async def sync_chain_miners_test(self):
        """Get registered mineres from testnet subnet 163"""
        self.model_manager.hotkey_store = get_mock_hotkeys_with_models()

    async def sync_chain_miners(self):
        """
        Updates hotkeys and downloads information of models from the chain
        """
        bt.logging.info("Selecting models for competition")
        bt.logging.info(f"Amount of hotkeys: {len(self.hotkeys)}")
        for hotkey in self.chain_miners_store.hotkeys:
            if self.chain_miners_store.hotkeys[hotkey] is None:
                continue
            try:
                model_info = await self.chain_miner_to_model_info(
                    self.chain_miners_store.hotkeys[hotkey]
                )
            except ValueError:
                bt.logging.warning(
                    f"Miner {hotkey} does not belong to this competition, skipping"
                )
                continue
            self.model_manager.hotkey_store[hotkey] = model_info

        bt.logging.info(
            f"Amount of hotkeys with valid models: {len(self.model_manager.hotkey_store)}"
        )

    async def evaluate(self) -> Tuple[str | None, ModelEvaluationResult | None]:
        """Returns hotkey and competition id of winning model miner"""
        bt.logging.info(f"Start of evaluation of {self.competition_id}")
        if self.test_mode:
            await self.sync_chain_miners_test()
        else:
            await self.sync_chain_miners()
        if len(self.model_manager.hotkey_store) == 0:
            bt.logging.error("No models to evaluate")
            return None, None
        await self.dataset_manager.prepare_dataset()
        X_test, y_test = await self.dataset_manager.get_data()

        competition_handler = COMPETITION_HANDLER_MAPPING[self.competition_id](
            X_test=X_test, y_test=y_test
        )

        y_test = competition_handler.prepare_y_pred(y_test)
        for miner_hotkey in self.model_manager.hotkey_store:
            bt.logging.info(f"Evaluating hotkey: {miner_hotkey}")
            model_or_none = await self.model_manager.download_miner_model(miner_hotkey)
            if not model_or_none:
                bt.logging.error(
                    f"Failed to download model for hotkey {miner_hotkey}  Skipping."
                )
                continue
            try:
                model_manager = ModelRunManager(
                    self.config, self.model_manager.hotkey_store[miner_hotkey]
                )
            except ModelRunException:
                bt.logging.error(
                    f"Model hotkey: {miner_hotkey} failed to initialize. Skipping"
                )
                continue
            start_time = time.time()

            try:
                y_pred = await model_manager.run(X_test)
            except ModelRunException:
                bt.logging.error(f"Model hotkey: {miner_hotkey} failed to run. Skipping")
                continue
            run_time_s = time.time() - start_time

            model_result = competition_handler.get_model_result(
                y_test, y_pred, run_time_s
            )
            self.results.append((miner_hotkey, model_result))
            if not self.test_mode:
                self.log_results_to_wandb(miner_hotkey, self.validator_hotkey, model_result)
        if len(self.results) == 0:
            bt.logging.error("No models were able to run")
            return None, None
        winning_hotkey, winning_model_result = sorted(
            self.results, key=lambda x: x[1].score, reverse=True
        )[0]
        for miner_hotkey, model_result in self.results:
            bt.logging.debug(
                f"Model result for {miner_hotkey}:\n {model_result.model_dump_json(indent=4)} \n"
            )

        bt.logging.info(
            f"Winning hotkey for competition {self.competition_id}: {winning_hotkey}"
        )
        return winning_hotkey, winning_model_result
