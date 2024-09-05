import asyncio
import copy
import time

import bittensor as bt
from dotenv import load_dotenv
from huggingface_hub import HfApi, login as hf_login
import huggingface_hub
import onnx
import argparse

from cancer_ai.validator.utils import run_command
from cancer_ai.validator.model_run_manager import ModelRunManager, ModelInfo
from cancer_ai.validator.dataset_manager import DatasetManager
from cancer_ai.validator.competition_manager import COMPETITION_HANDLER_MAPPING

from cancer_ai.base.base_miner import BaseNeuron
from cancer_ai.chain_models_store import ChainMinerModel, ChainModelMetadataStore
from cancer_ai.utils.config import path_config, add_miner_args


class MinerManagerCLI:
    def __init__(self, config=None):

        # setting basic Bittensor objects
        base_config = copy.deepcopy(config or BaseNeuron.config())
        self.config = path_config(self)
        self.config.merge(base_config)
        self.config.logging.debug = True
        BaseNeuron.check_config(self.config)
        bt.logging.set_config(config=self.config.logging)

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        """Method for injecting miner arguments to the parser."""
        add_miner_args(cls, parser)

    async def upload_to_hf(self) -> None:
        """Uploads model and code to Hugging Face."""
        bt.logging.info("Uploading model to Hugging Face.")
        hf_api = HfApi()
        hf_login(token=self.config.hf_token)

        hf_model_path = f"{self.config.competition.id}-{self.config.hf_model_name}.onnx"
        hf_code_path = f"{self.config.competition.id}-{self.config.hf_model_name}.zip"

        path = hf_api.upload_file(
            path_or_fileobj=self.config.model_path,
            path_in_repo=hf_model_path,
            repo_id=self.config.hf_repo_id,
            repo_type="model",
            token=self.config.hf_token,
        )
        bt.logging.info("Uploading code to Hugging Face.")
        path = hf_api.upload_file(
            path_or_fileobj=self.code_zip_path,
            path_in_repo=hf_code_path,
            repo_id=self.config.hf_repo_id,
            repo_type="model",
            token=self.config.hf_token,
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
            self.config.competition.id,
            "safescanai/test_dataset",
            "test_dataset.zip",
            "dataset",
        )
        await dataset_manager.prepare_dataset()

        X_test, y_test = await dataset_manager.get_data()

        competition_handler = COMPETITION_HANDLER_MAPPING[self.config.competition.id](
            X_test=X_test, y_test=y_test
        )

        y_test = competition_handler.prepare_y_pred(y_test)

        start_time = time.time()
        y_pred = await run_manager.run(X_test)
        run_time_s = time.time() - start_time
        
        # print(y_pred)
        model_result = competition_handler.get_model_result(y_test, y_pred, run_time_s)
        bt.logging.info(
            f"Evalutaion results:\n{model_result.model_dump_json(indent=4)}"
        )
        if self.config.clean_after_run:
            dataset_manager.delete_dataset()

    async def compress_code(self) -> None:
        bt.logging.info("Compressing code")
        code_zip_path = f"{self.config.code_directory}/code.zip"
        out, err = await run_command(
            f"zip  -r {code_zip_path} {self.config.code_directory}/*"
        )
        if err:
            "Error zipping code"
            bt.logging.error(err)
            return
        bt.logging.info(f"Code zip path: {code_zip_path}")
        self.code_zip_path = code_zip_path

    async def submit_model(self) -> None:
        # Check if the required model and files are present in hugging face repo

        self.wallet = bt.wallet(config=self.config)
        self.subtensor = bt.subtensor(config=self.config)
        self.metagraph = self.subtensor.metagraph(self.config.netuid)
        bt.logging.info(f"Wallet: {self.wallet}")
        bt.logging.info(f"Subtensor: {self.subtensor}")
        bt.logging.info(f"Metagraph: {self.metagraph}")
        if not self.subtensor.is_hotkey_registered(
            netuid=self.config.netuid,
            hotkey_ss58=self.wallet.hotkey.ss58_address,
        ):
            bt.logging.error(
                f"Wallet: {self.wallet} is not registered on netuid {self.config.netuid}."
                f" Please register the hotkey using `btcli subnets register` before trying again"
            )
            exit()
        self.metadata_store = ChainModelMetadataStore(
            subtensor=self.subtensor, subnet_uid=self.config.netuid, wallet=self.wallet
        )

        if not huggingface_hub.file_exists(
            repo_id=self.config.hf_repo_id,
            filename=self.config.hf_model_name,
            repo_type=self.config.hf_repo_type,
        ):
            bt.logging.error(
                f"{self.config.hf_model_name} not found in Hugging Face repo"
            )
            return

        if not huggingface_hub.file_exists(
            repo_id=self.config.hf_repo_id,
            filename=self.config.hf_code_filename,
            repo_type=self.config.hf_repo_type,
        ):
            bt.logging.error(
                f"{self.config.hf_model_name} not found in Hugging Face repo"
            )
            return
        bt.logging.info("Model and code found in Hugging Face repo")

        # Push model metadata to chain
        model_id = ChainMinerModel(
            competition_id=self.config.competition.id,
            hf_repo_id=self.config.hf_repo_id,
            hf_model_filename=self.config.hf_model_name,
            hf_repo_type=self.config.hf_repo_type,
            hf_code_filename=self.config.hf_code_filename,
            block=None,
        )
        await self.metadata_store.store_model_metadata(model_id)
        bt.logging.success(
            f"Successfully pushed model metadata on chain. Model ID: {model_id}"
        )

    async def main(self) -> None:
        # bt.logging(config=self.config)
        if not self.config.model_path:
            bt.logging.error("Missing --model-path argument")
            return
        if not MinerManagerCLI.is_onnx_model(self.config.model_path):
            bt.logging.error("Provided model with is not in ONNX format")
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
    load_dotenv()
    cli_manager = MinerManagerCLI()
    asyncio.run(cli_manager.main())
