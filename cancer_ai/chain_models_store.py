import functools
import bittensor as bt
import datetime
from typing import ClassVar, Optional, Type

from .utils.models_storage_utils import run_in_subprocess
from pydantic import BaseModel, Field, PositiveInt


class ChainMinerModel(BaseModel):
    """Uniquely identifies a trained model"""

    namespace: str = Field(
        description="Namespace where the model can be found. ex. Hugging Face username/org."
    )
    name: str = Field(description="Name of the model.")

    epoch: int = Field(
        description="The epoch number to submit as your checkpoint to evaluate e.g. 10"
    )

    date: datetime.datetime = Field(
        description="The datetime at which model was pushed to hugging face"
    )

    # Identifier for competition
    competition_id: Optional[str] = Field(description="The competition id")

    block: Optional[str] = Field(
        description="Block on which this model was claimed on the chain."
    )

    hf_repo_id: Optional[str] = Field(description="Hugging Face repo id.")
    hf_filename: Optional[str] = Field(description="Hugging Face filename.")
    hf_repo_type: Optional[str] = Field(description="Hugging Face repo type.")

    class Config:
        arbitrary_types_allowed = True

    def to_compressed_str(self) -> str:
        """Returns a compressed string representation."""
        return f"{self.namespace}:{self.name}:{self.epoch}:{self.competition_id}:{self.date}"

    @classmethod
    def from_compressed_str(cls, cs: str) -> Type["ChainMinerModel"]:
        """Returns an instance of this class from a compressed string representation"""
        tokens = cs.split(":")
        return cls(
            namespace=tokens[0],
            name=tokens[1],
            epoch=tokens[2] if tokens[2] != "None" else None,
            date=tokens[3] if tokens[3] != "None" else None,
            competition_id=tokens[4] if tokens[4] != "None" else None,
        )


class ChainModelMetadataStore:
    """Chain based implementation for storing and retrieving metadata about a model."""

    def __init__(
        self,
        subtensor: bt.subtensor,
        subnet_uid: int,
        wallet: Optional[bt.wallet] = None,
    ):
        self.subtensor = subtensor
        self.wallet = (
            wallet  # Wallet is only needed to write to the chain, not to read.
        )
        self.subnet_uid = subnet_uid

    async def store_model_metadata(self, model_id: ChainMinerModel):
        """Stores model metadata on this subnet for a specific wallet."""
        if self.wallet is None:
            raise ValueError("No wallet available to write to the chain.")

        # Wrap calls to the subtensor in a subprocess with a timeout to handle potential hangs.
        partial = functools.partial(
            self.subtensor.commit,
            self.wallet,
            self.subnet_uid,
            model_id.to_compressed_str(),
        )
        run_in_subprocess(partial, 60)

    async def retrieve_model_metadata(self, hotkey: str) -> Optional[ChainMinerModel]:
        """Retrieves model metadata on this subnet for specific hotkey"""

        # Wrap calls to the subtensor in a subprocess with a timeout to handle potential hangs.
        partial = functools.partial(
            bt.extrinsics.serving.get_metadata, self.subtensor, self.subnet_uid, hotkey
        )

        metadata = run_in_subprocess(partial, 60)
        if not metadata:
            return None
        print("piwo", metadata["info"]["fields"])
        commitment = metadata["info"]["fields"][0]
        hex_data = commitment[list(commitment.keys())[0]][2:]

        chain_str = bytes.fromhex(hex_data).decode()

        try:
            model = ChainMinerModel.from_compressed_str(chain_str)
        except:
            # If the metadata format is not correct on the chain then we return None.
            bt.logging.error(
                f"Failed to parse the metadata on the chain for hotkey {hotkey}. Raw value: {chain_str}"
            )
            return None
        # The block id at which the metadata is stored
        model.block = metadata["block"]
        return model
