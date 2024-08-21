import argparse

import bittensor as bt
from dotenv import load_dotenv

from cancer_ai.validator.utils import ModelType
from huggingface_hub import HfApi
import onnx
import asyncio

from .miner_config import get_config


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
    model = onnx.load(model_path)
    assert model is not None, "Failed to load model"
    assert model.ir_version > 0, "Model is not an ONNX model"


async def main(config: bt.config) -> None:
    bt.logging(config=config)
    print(config)
    if not is_onnx_model(config.model_path):
        bt.logging.error("Provided model with --model_type is not in ONNX format")
        return
    match config.action:
        case  "submit":
            # The wallet holds the cryptographic key pairs for the miner.
            bt.logging.info("Initializing connection with Bittensor subnet {config.netuid} - Safe-Scan Project")
            bt.logging.info(f"Subtensor network: {config.subtensor.network}")
            bt.logging.info(f"Wallet hotkey: {config.wallet.hotke.ss58_address}")
            wallet = bt.wallet(config=config)
            subtensor = bt.subtensor(config=config)
            metagraph = subtensor.metagraph(config.netuid)

            # Start miner
            bt.logging.info("Starting miner.")
        case  "evaluate":
            pass
        case "upload":
            bt.logging.info("Uploading model to Hugging Face.")
            bt.huggingface(config=config)
        case _:
            bt.logging.error(f"Unrecognized action: {config.action}")


if __name__ == "__main__":
    config = get_config()
    print(config)
    load_dotenv()
    asyncio.run(main(config))
    
