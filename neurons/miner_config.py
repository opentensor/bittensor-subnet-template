import argparse

import bittensor as bt

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


def get_config() -> bt.config:
    main_parser = argparse.ArgumentParser()
    # always required
    main_parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to ONNX model, used for evaluation",
    )
    main_parser.add_argument(
        "--competition_id",
        type=str,
        help="Competition ID",
        required=True,
    )
    # common arguments for subparsers
    def add_hf_arguments(parser: argparse.ArgumentParser) -> None:
        """Adds Hugging Face arguments to the parser."""
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
    subparsers = main_parser.add_subparsers(title="action")
    subparser_evaluate = subparsers.add_parser("evaluate")

    subparser_upload = subparsers.add_parser("upload")
    add_hf_arguments(subparser_upload)

    subparser_submit = subparsers.add_parser("submit")
    add_hf_arguments(subparser_submit)

    bt.wallet.add_args(main_parser)
    bt.subtensor.add_args(main_parser)
    bt.logging.add_args(main_parser)

    config = bt.config(main_parser)
    return config
