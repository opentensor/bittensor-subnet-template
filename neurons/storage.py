import concurrent
import time
from typing import Optional

import bittensor as bt
from bittensor.extrinsics import serving
from pydantic import BaseModel
from websocket import WebSocketConnectionClosedException

from insights.protocol import get_network_id, get_model_id
from neurons import VERSION
from neurons.docker_utils import get_docker_image_version

class Metadata(BaseModel):
    def to_compact(self):
        return ','.join(f"{key}:{repr(getattr(self, key))}" for key in self.__dict__)

class MinerMetadata(Metadata):
    b: int
    v: int
    di: str
    n: int
    mt: int
    ri: str

    @staticmethod
    def from_compact(compact_str):
        data_dict = {}
        for item in compact_str.split(','):
            key, value = item.split(':', 1)
            data_dict[key] = value.strip("'")
        return MinerMetadata(**data_dict)

class ValidatorMetadata(Metadata):
    b: int
    v: int
    di: str

    @staticmethod
    def from_compact(compact_str):
        data_dict = {}
        for item in compact_str.split(','):
            key, value = item.split(':', 1)
            data_dict[key] = value.strip("'")
        return ValidatorMetadata(**data_dict)

def get_commitment_wrapper(subtensor, netuid, _, hotkey, block=None):
    def get_commitment():
        metadata = serving.get_metadata(subtensor, netuid, hotkey, block)
        if metadata is None:
            return None
        commitment = metadata["info"]["fields"][0]
        hex_data = commitment[list(commitment.keys())[0]][2:]
        return bytes.fromhex(hex_data).decode()

    return get_commitment()

def store_miner_metadata(config, graph_search, wallet):
    def get_metadata():
        run_id = graph_search.get_run_id()
        docker_image = get_docker_image_version()
        return MinerMetadata(
            b=subtensor.block,
            n=get_network_id(config.network),
            mt=get_model_id(config.model_type),
            v=VERSION,
            di=docker_image,
            ri=run_id,
        )

    subtensor = bt.subtensor(config=config)

    try:
        metadata = get_metadata()
        subtensor.commit(wallet, config.netuid, Metadata.to_compact(metadata))
        bt.logging.info(f"Stored miner metadata: {metadata}")
    except bt.errors.MetadataError as e:
        bt.logging.warning(f"Skipping storing miner metadata")

def store_validator_metadata(config, wallet):

    subtensor = bt.subtensor(config=config)

    try:
        docker_image = get_docker_image_version()
        metadata =  ValidatorMetadata(
            b=subtensor.block,
            v=VERSION,
            di=docker_image,
        )
        subtensor.commit(wallet, config.netuid, metadata.to_compact())
        bt.logging.info(f"Stored validator metadata: {metadata}")
    except bt.errors.MetadataError as e:
        bt.logging.warning(f"Skipping storing validator metadata")

def get_miners_metadata(config, metagraph):
    miners_metadata = {}
    bt.logging.info(f"Getting miner's metadata")

    subtensor = bt.subtensor(config=config)
    for axon in metagraph.axons:
        if axon.is_serving:
            hotkey = axon.hotkey
            def get_commitment(netuid: int, uid: int, block: Optional[int] = None) -> str:
                metadata = serving.get_metadata(subtensor, netuid, hotkey, block)
                if metadata is None:
                    return None
                commitment = metadata["info"]["fields"][0]
                hex_data = commitment[list(commitment.keys())[0]][2:]
                return bytes.fromhex(hex_data).decode()

            subtensor.get_commitment = get_commitment
            try:
                metadata_str = subtensor.get_commitment(config.netuid, 0)
                if metadata_str is None:
                    continue
                metadata = MinerMetadata.from_compact(metadata_str)
                miners_metadata[hotkey] = metadata
            except:
                bt.logging.warning(f"Error while getting validator metadata for {hotkey}, Skipping...")
                continue

    return miners_metadata

def get_validator_metadata(config, metagraph):
    validator_metadata = {}

    subtensor = bt.subtensor(config=config)

    for neuron in metagraph.neurons:
        if neuron.axon_info.ip == '0.0.0.0':
            hotkey = neuron.hotkey
            uid = neuron.uid

            bt.logging.info(f"Getting validator metadata for {hotkey}")

            def get_commitment(netuid: int, uid: int, block: Optional[int] = None) -> str:
                metadata = serving.get_metadata(subtensor, netuid, hotkey, block)
                if metadata is None:
                    return None
                commitment = metadata["info"]["fields"][0]
                hex_data = commitment[list(commitment.keys())[0]][2:]
                return bytes.fromhex(hex_data).decode()

            subtensor.get_commitment = get_commitment

            try:
                metadata_str = subtensor.get_commitment(config.netuid, uid)
                if metadata_str is None:
                    continue
                metadata = ValidatorMetadata.from_compact(metadata_str)
                validator_metadata[hotkey] = metadata
            except:
                bt.logging.warning(f"Error while getting validator metadata for {hotkey}, Skipping...")
                continue

    bt.logging.info(f"validators metadata: {validator_metadata}")
    return validator_metadata