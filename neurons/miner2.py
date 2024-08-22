import argparse
import sys

import bittensor as bt
from dotenv import load_dotenv
from huggingface_hub import HfApi
import onnx
import asyncio

from neurons.miner_config import get_config

from cancer_ai.validator.utils import ModelType
from cancer_ai.validator.model_run_manager import ModelRunManager, ModelInfo
from cancer_ai.validator.dataset_manager import DatasetManager
from cancer_ai.validator.model_manager import ModelManager


async def test_model(config: bt.config, model_path: str):
    pass


def upload_model_to_hf(self) -> None:
    """Uploads model to Hugging Face."""
    hf_api = HfApi()
    hf_api.upload_file(
        path_or_fileobj=self.config.models.model_path,
    )


def is_onnx_model(model_path: str) -> None:
    """Checks if model is an ONNX model."""
    try:
        onnx.checker.check_model(model_path)
    except onnx.checker.ValidationError as e:
        print(e)
        return False
    return True


async def evaluate_model(config: bt.config) -> None:
    bt.logging.info("Evaluate model mode")
    run_manager = ModelRunManager(
        config=config, model=ModelInfo(file_path=config.model_path)
    )
    dataset_manager = DatasetManager(
        config,
        config.competition_id,
        "safescanai/test_dataset",
        "skin_melanoma.zip",
    )
    await dataset_manager.prepare_dataset()

    pred_x, pred_y = await dataset_manager.get_data()

    model_predictions = await run_manager.run(pred_x)

    print(pred_y)
    print(model_predictions)

    if config.clean_after_run:
        dataset_manager.delete_dataset()


async def main(config: bt.config) -> None:
    bt.logging(config=config)

    if not is_onnx_model(config.model_path):
        bt.logging.error("Provided model with --model_type is not in ONNX format")
        return

    match config.action:
        case "submit":
            # The wallet holds the cryptographic key pairs for the miner.
            bt.logging.info(
                "Initializing connection with Bittensor subnet {config.netuid} - Safe-Scan Project"
            )
            bt.logging.info(f"Subtensor network: {config.subtensor.network}")
            bt.logging.info(f"Wallet hotkey: {config.wallet.hotke.ss58_address}")
            wallet = bt.wallet(config=config)
            subtensor = bt.subtensor(config=config)
            metagraph = subtensor.metagraph(config.netuid)

            # Start miner
            bt.logging.info("Starting miner.")
        case "evaluate":
            await evaluate_model(config)

        case "upload":
            bt.logging.info("Uploading model to Hugging Face.")
            bt.huggingface(config=config)
        case _:
            bt.logging.error(f"Unrecognized action: {config.action}")


if __name__ == "__main__":
    config = get_config()
    load_dotenv()
    asyncio.run(main(config))
