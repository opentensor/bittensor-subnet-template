import argparse

import bittensor as bt
from dotenv import load_dotenv

from cancer_ai.validator.utils import ModelType
from huggingface_hub import HfApi
import onnx

help = """
How to run it:

python3 neurons/miner2.py  \
    evaluate \
    --logging.debug \
    --model_type pytorch \
    --model_path /path/to/model \
    --competition_id  "your_competition_id"

python3 upload neurons/miner2.py \
    --model_path /path/to/model
    --hf_repo_id "hf_org_id/your_hf_repo_id"
    
python3 neurons/miner2.py \
    submit \
    --netuid 163 \
    --subtensor.network test \
    --wallet.name miner \
    --wallet.hotkey hot_validator \
    --model_type pytorch \
    --model_path /path/to/model
"""


def get_config() -> bt.config:
    parser = argparse.ArgumentParser()

    # always required
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to ONNX model, used for evaluation",
    )
    parser.add_argument(
        "--model_type",
        type=str,
        help="Type of model to use",
        required=True,
        choices=list(ModelType),
    )
    parser.add_argument(
        "--competition_id",
        type=str,
        help="Competition ID",
        required=True,
    )

    # common arguments for subparsers
    def add_hf_arguments(parser):
        parser.add_argument(
            "--hf_repo_id",
            type=str,
            default=None,
            help="Hugging Face model repository ID",
        )
        parser.add_argument(
            "--hf_file_path",
            type=str,
            default=None,
            help="Hugging Face model file path",
        )

    subparsers = parser.add_subparsers(required=True)

    subparser_evaluate = subparsers.add_parser("evaluate")

    subparser_upload = subparsers.add_parser("upload")
    add_hf_arguments(subparser_upload)

    subparser_submit = subparsers.add_parser("submit")
    add_hf_arguments(subparser_submit)

    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)

    config = bt.config(parser)
    return config


async def test_model(config: bt.config, model_path: str, model_type: str):
    pass


def upload_model_to_hf(self) -> None:
    """Uploads model to Hugging Face."""
    hf_api = HfApi()
    hf_api.upload_file(
        path_or_fileobj=self.config.models.model_path,
    )


def is_it_onnx_model(model_path: str) -> None:
    """Checks if model is an ONNX model."""
    model = onnx.load(model_path)
    assert model is not None, "Failed to load model"
    assert model.ir_version > 0, "Model is not an ONNX model"


async def main(config: bt.config) -> None:
    bt.logging(config=config)
    if not is_it_onnx_model(config.models.model_path):
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
            bt.logging.error(f"Unrecognized action: {action}")

    else:
        bt.logging.error(f"Unrecognized action: {action}")


if __name__ == "__main__":
    config = get_config()
    load_dotenv()
    main(config)
