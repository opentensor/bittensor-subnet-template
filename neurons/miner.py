import asyncio

import bittensor as bt
from dotenv import load_dotenv
from huggingface_hub import HfApi
import huggingface_hub
import onnx
import cancer_ai
import typing

from cancer_ai.validator.utils import run_command
from cancer_ai.validator.model_run_manager import ModelRunManager, ModelInfo
from cancer_ai.validator.dataset_manager import DatasetManager
from cancer_ai.base.miner import BaseMinerNeuron
from cancer_ai.chain_models_store import ChainMinerModel, ChainModelMetadataStore


class MinerManagerCLI(BaseMinerNeuron):
    def __init__(self, config=None):
        super(MinerManagerCLI, self).__init__(config=config)
        self.metadata_store = ChainModelMetadataStore(
            subtensor=self.subtensor, subnet_uid=self.config.netuid, wallet=self.wallet
        )
        self.hf_api = HfApi()

    # TODO: Dive into BaseNeuron to switch off requirement to implement legacy methods, for now they are mocked.
    async def forward(
        self, synapse: cancer_ai.protocol.Dummy
    ) -> cancer_ai.protocol.Dummy: ...

    async def blacklist(
        self, synapse: cancer_ai.protocol.Dummy
    ) -> typing.Tuple[bool, str]: ...

    async def priority(self, synapse: cancer_ai.protocol.Dummy) -> float: ...

    async def upload_to_hf(self) -> None:
        """Uploads model and code to Hugging Face."""
        bt.logging.info("Uploading model to Hugging Face.")
        path = self.hf_api.upload_file(
            path_or_fileobj=self.config.model_path,
            path_in_repo=f"{self.config.competition_id}-{self.config.hf_model_name}.onnx",
            repo_id=self.config.hf_repo_id,
            repo_type="model",
            token=self.config.hf_token,
        )
        bt.logging.info("Uploading code to Hugging Face.")
        path = self.hf_api.upload_file(
            path_or_fileobj=f"{self.config.code_directory}/code.zip",
            path_in_repo=f"{self.config.competition_id}-{self.config.hf_model_name}.zip",
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
            "safescanai/test_dataset",
            "skin_melanoma.zip",
            "dataset",
        )
        await dataset_manager.prepare_dataset()

        pred_x, pred_y = await dataset_manager.get_data()

        model_predictions = await run_manager.run(pred_x)

        if self.config.clean_after_run:
            dataset_manager.delete_dataset()

    async def compress_code(self) -> str:
        bt.logging.info("Compressing code")
        out, err = await run_command(
            f"zip  {self.config.code_directory}/code.zip {self.config.code_directory}/*"
        )
        return f"{self.config.code_directory}/code.zip"

    async def submit_model(self) -> None:
        # Check if the required model and files are present in hugging face repo
        filenames = [
            self.config.hf_model_name + ".onnx",
            self.config.hf_model_name + ".zip",
        ]
        for file in filenames:
            if not huggingface_hub.file_exists(
                repo_id=self.config.hf_repo_id,
                filename=file,
                token=self.config.hf_token,
            ):
                bt.logging.error(f"{file} not found in Hugging Face repo")
                return
        bt.logging.info("Model and code found in Hugging Face repo")

        # Push model metadata to chain
        model_id = ChainMinerModel(
            competition_id=self.config.competition_id,
            hf_repo_id=self.config.hf_repo_id,
            hf_repo_type=self.config.hf_repo_type,
            hf_model_name=self.config.hf_model_name,
            hf_model_filename=self.config.hf_model_name + ".onnx",
            hf_code_filename=self.config.hf_model_name + ".zip",
        )
        await self.metadata_store.store_model_metadata(model_id)
        bt.logging.success(
            f"Successfully pushed model metadata on chain. Model ID: {model_id}"
        )

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
    cli_manager = MinerManagerCLI()
    asyncio.run(cli_manager.main())
