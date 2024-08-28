import argparse

from colorama import init, Fore, Back, Style
import bittensor as bt
from bittensor.btlogging import format


help = """
How to run it:

python3 neurons/miner2.py  \
    evaluate \
    --logging.debug \
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
    --model_path /path/to/model
"""
import argparse
import bittensor as bt

import argparse


def set_log_formatting() -> None:
    """Override bittensor logging formats."""
    

    format.LOG_TRACE_FORMATS = {
        level: f"{Fore.BLUE}%(asctime)s{Fore.RESET}"
        f" | {Style.BRIGHT}{color}%(levelname)s{Fore.RESET}{Back.RESET}{Style.RESET_ALL}"
        f" |%(message)s"
        for level, color in format.log_level_color_prefix.items()
    }

    format.DEFAULT_LOG_FORMAT = (
        f"{Fore.BLUE}%(asctime)s{Fore.RESET} | "
        f"{Style.BRIGHT}{Fore.WHITE}%(levelname)s{Style.RESET_ALL} | "
        "%(message)s"
    )

    format.DEFAULT_TRACE_FORMAT = (
        f"{Fore.BLUE}%(asctime)s{Fore.RESET} | "
        f"{Style.BRIGHT}{Fore.WHITE}%(levelname)s{Style.RESET_ALL} | "
        f" %(message)s"
    )


def get_config() -> bt.config:
    main_parser = argparse.ArgumentParser()

    main_parser.add_argument(
        "--action",
        choices=["submit", "evaluate", "upload"],
        # required=True,
        default="evaluate",
    )
    main_parser.add_argument(
        "--model_path",
        type=str,
        # required=True,
        help="Path to ONNX model, used for evaluation",
        default="neurons/simple_cnn_model.onnx",
    )
    main_parser.add_argument(
        "--competition_id",
        type=str,
        # required=True,
        help="Competition ID",
        default="melanoma-1",
    )

    main_parser.add_argument(
        "--dataset_dir",
        type=str,
        help="Path for storing datasets.",
        default="./datasets",
    )
    # Subparser for upload command

    main_parser.add_argument(
        "--hf_repo_id",
        type=str,
        required=False,
        help="Hugging Face model repository ID",
        default="eatcats/melanoma-test",
    )

    main_parser.add_argument(
        "--clean-after-run",
        action="store_true",
        help="Whether to clean up (dataset, temporary files) after running",
        default=False,
    )
    main_parser.add_argument(
        "--code-directory",
        type=str,
        help="Path to code directory",
        default=".",
    )

    # Add additional args from bt modules
    bt.wallet.add_args(main_parser)
    bt.subtensor.add_args(main_parser)
    bt.logging.add_args(main_parser)

    # Parse the arguments and return the config
    # config = bt.config(main_parser)
    # parsed = main_parser.parse_args()
    # config = bt.config(main_parser)
    

    config = main_parser.parse_args()
    config.logging_dir = "./"
    config.record_log = True
    config.trace = True
    config.debug = False
    return config


if __name__ == "__main__":
    config = get_config()
    print(config)
