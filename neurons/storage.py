from typing import Optional

import bittensor as bt
from pydantic import BaseModel

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

def store_miner_metadata(config, uid, graph_search, wallet, subtensor):
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

    try:
        metadata = get_metadata()
        subtensor.commit(wallet, config.netuid, Metadata.to_compact(metadata))
        bt.logging.info(f"Stored miner metadata: {metadata}")
    except bt.errors.MetadataError as e:
        bt.logging.warning(f"Skipping storing miner metadata")

def get_miners_metadata(config, subtensor, metagraph):
    miners_metadata = {}
    for axon in metagraph.axons:
        if axon.is_serving:
            try:
                hotkey = axon.hotkey
                uid = subtensor.get_uid_for_hotkey_on_subnet(hotkey, config.netuid)
                metadata_str = subtensor.get_commitment(config.netuid, uid)
                if metadata_str is not None:
                    miners_metadata[hotkey] = MinerMetadata.from_compact(metadata_str)
            except:
                pass

    return miners_metadata

def store_validator_metadata(config, wallet, subtensor):
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

def get_validator_metadata(config, subtensor, metagraph):
    validator_metadata = {}
    bt.logging.info(f"Getting validator metadata...")
    for neuron in metagraph.neurons:
        if neuron.axon_info.ip == '0.0.0.0':
            hotkey = neuron.hotkey
            try:
                uid = subtensor.get_uid_for_hotkey_on_subnet(hotkey, config.netuid)
                metadata_str = subtensor.get_commitment(config.netuid, uid)
                if metadata_str is not None:
                    validator_metadata[hotkey] = ValidatorMetadata.from_compact(metadata_str)
                    bt.logging.info(f"Updated validator metadata for: {validator_metadata[hotkey]}")
            except Exception as e:
                bt.logging.warning(f"Error while getting validator metadata for {hotkey}")

    bt.logging.info(f"Got validator metadata: {validator_metadata}")
    return validator_metadata