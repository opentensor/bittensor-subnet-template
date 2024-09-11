import functools
from typing import Optional, Type

import bittensor as bt
from pydantic import BaseModel, Field

from .utils.models_storage_utils import run_in_subprocess


class ChainMinerModel(BaseModel):
    """Uniquely identifies a trained model"""

    competition_id: Optional[str] = Field(description="The competition id")
    hf_repo_id: Optional[str] = Field(description="Hugging Face repository id.")
    hf_model_filename: Optional[str] = Field(description="Hugging Face model filename.")
    hf_repo_type: Optional[str] = Field(
        description="Hugging Face repository type.", default="model"
    )
    hf_code_filename: Optional[str] = Field(
        description="Hugging Face code zip filename."
    )
    block: Optional[int] = Field(
        description="Block on which this model was claimed on the chain."
    )

    class Config:
        arbitrary_types_allowed = True

    def to_compressed_str(self) -> str:
        """Returns a compressed string representation."""
        return f"{self.hf_repo_id}:{self.hf_model_filename}:{self.hf_code_filename}:{self.competition_id}:{self.hf_repo_type}"

    @classmethod
    def from_compressed_str(cls, cs: str) -> Type["ChainMinerModel"]:
        """Returns an instance of this class from a compressed string representation"""
        tokens = cs.split(":")
        if len(tokens) != 5:
            return None
        return cls(
            hf_repo_id=tokens[0],
            hf_model_filename=tokens[1],
            hf_code_filename=tokens[2],
            competition_id=tokens[3],
            hf_repo_type=tokens[4],
            block=None,
        )


class ChainMinerModelStore(BaseModel):
    hotkeys: dict[str, ChainMinerModel | None]
    last_updated: float | None = None


class ChainModelMetadata:
    """Chain based implementation for storing and retrieving metadata about a model."""

    def __init__(
        self,
        subtensor: bt.subtensor,
        netuid: int,
        wallet: Optional[bt.wallet] = None,
    ):
        self.subtensor = subtensor
        self.wallet = (
            wallet  # Wallet is only needed to write to the chain, not to read.
        )
        self.netuid = netuid

    async def store_model_metadata(self, model_id: ChainMinerModel):
        """Stores model metadata on this subnet for a specific wallet."""
        if self.wallet is None:
            raise ValueError("No wallet available to write to the chain.")

        # Wrap calls to the subtensor in a subprocess with a timeout to handle potential hangs.
        partial = functools.partial(
            self.subtensor.commit,
            self.wallet,
            self.netuid,
            model_id.to_compressed_str(),
        )
        run_in_subprocess(partial, 60)

    async def retrieve_model_metadata(self, hotkey: str) -> Optional[ChainMinerModel]:
        """Retrieves model metadata on this subnet for specific hotkey"""
        # Wrap calls to the subtensor in a subprocess with a timeout to handle potential hangs.
        try:
            metadata = bt.extrinsics.serving.get_metadata(
                self.subtensor, self.netuid, hotkey
            )
        except Exception as e:
            bt.logging.error(f"Error retrieving metadata for hotkey {hotkey}: {e}")
            return None
        if not metadata:
            return None
        bt.logging.trace(f"Model metadata: {metadata['info']['fields']}")
        commitment = metadata["info"]["fields"][0]
        hex_data = commitment[list(commitment.keys())[0]][2:]

        chain_str = bytes.fromhex(hex_data).decode()
        try:
            model = ChainMinerModel.from_compressed_str(chain_str)
            bt.logging.debug(f"Model: {model}")
            if model is None:
                bt.logging.error(
                    f"Metadata might be in old format on the chain for hotkey {hotkey}. Raw value: {chain_str}"
                )
                return None
        except:
            # If the metadata format is not correct on the chain then we return None.
            bt.logging.error(
                f"Failed to parse the metadata on the chain for hotkey {hotkey}. Raw value: {chain_str}"
            )
            return None
        # The block id at which the metadata is stored
        model.block = metadata["block"]
        return model
