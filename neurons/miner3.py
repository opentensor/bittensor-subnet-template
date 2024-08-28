import argparse
import sys
import asyncio
from typing import Optional

import bittensor as bt
from dotenv import load_dotenv
from huggingface_hub import HfApi
import onnx

from neurons.miner_config import get_config, set_log_formatting
from cancer_ai.validator.utils import ModelType, run_command
from cancer_ai.validator.model_run_manager import ModelRunManager, ModelInfo
from cancer_ai.validator.dataset_manager import DatasetManager
from cancer_ai.validator.model_manager import ModelManager
from datetime import datetime


class MinerManagerCLI:
    def __init__(self, config: bt.config):
        self.config = config
        self.hf_api = HfApi()

    async def upload_to_hf(self) -> None:
        """Uploads model and code to Hugging Face."""
        bt.logging.info("Uploading model to Hugging Face.")
        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = self.hf_api.upload_file(
            path_or_fileobj=self.config.model_path,
            path_in_repo=f"{now_str}-{self.config.competition_id}.onnx",
            repo_id=self.config.hf_repo_id,
            repo_type="model",
        )
        path = self.hf_api.upload_file(
            path_or_fileobj=f"{self.config.code_directory}/code.zip",
            path_in_repo=f"{now_str}-{self.config.competition_id}.zip",
            repo_id=self.config.hf_repo_id,
            repo_type="model",
        )

        bt.logging.info(f"Uploaded model to Hugging Face: {path}")

    @staticmethod
    def is_onnx_model(model_path: str) -> bool:
        """Checks if model is an ONNX model."""
        try:
            onnx.checker.check_model(model_path)
        except onnx.checker.ValidationError as e:
            bt.logging.warning(e)
            return False
        return True

    async def evaluate_model(self) -> None:
        bt.logging.info("Evaluate model mode")
        run_manager = ModelRunManager(
            config=self.config, model=ModelInfo(file_path=self.config.model_path)
        )
        dataset_manager = DatasetManager(
            self.config,
            self.config.competition_id,
            "safescanai/test_dataset",
            "skin_melanoma.zip",
            "dataset",
        )
        await dataset_manager.prepare_dataset()

        pred_x, pred_y = await dataset_manager.get_data()

        model_predictions = await run_manager.run(pred_x)

        print(pred_y)
        print(model_predictions)

        if self.config.clean_after_run:
            dataset_manager.delete_dataset()

    async def compress_code(self) -> str:
        bt.logging.info("Compressing code")
        out, err = await run_command(
            f"zip  {self.config.code_directory}/code.zip {self.config.code_directory}/*"
        )
        return f"{self.config.code_directory}/code.zip"

    async def submit_model(self) -> None:
        bt.logging.info(
            f"Initializing connection with Bittensor subnet {self.config.netuid} - Safe-Scan Project"
        )
        bt.logging.info(f"Subtensor network: {self.config.subtensor.network}")
        bt.logging.info(f"Wallet hotkey: {self.config.wallet.hotkey.ss58_address}")
        wallet = self.wallet
        subtensor = self.subtensor
        metagraph = self.metagraph

    async def main(self) -> None:
        bt.logging(config=self.config)

        if not self.is_onnx_model(self.config.model_path):
            bt.logging.error("Provided model with --model_type is not in ONNX format")
            return

        match self.config.action:
            case "submit":
                await self.submit_model()
            case "evaluate":
                await self.evaluate_model()
            case "upload":
                await self.compress_code()
                await self.upload_to_hf()
            case _:
                bt.logging.error(f"Unrecognized action: {self.config.action}")


if __name__ == "__main__":
    from types import SimpleNamespace
    config = get_config()
    config = {
        "dataset_dir": "./data",
    }
    config = SimpleNamespace( **config)
    set_log_formatting()
    load_dotenv()
    cli_manager = MinerManagerCLI(config)
    asyncio.run(cli_manager.main())
