from typing import Optional, List

import insights

import bittensor as bt
from bittensor.extrinsics import serving
from pydantic import BaseModel
from insights.protocol import get_network_id

class Metadata(BaseModel):
    def to_compact(self):
        return ','.join(f"{key}:{repr(getattr(self, key))}" for key in self.__dict__)

class MinerMetadata(Metadata):
    sb: Optional[int] #start_block_height
    lb: Optional[int] #end_block_height
    bl: Optional[int] #balance_model_last_block_height
    n: Optional[int] #network
    cv: Optional[str] #code_version
    
    @staticmethod
    def from_compact(compact_str):
        data_dict = {}
        for item in compact_str.split(','):
            key, value = item.split(':', 1)
            data_dict[key] = value.strip("'")
        return MinerMetadata(**data_dict)

class ValidatorMetadata(Metadata):
    cv: Optional[str] #code_version
    ip: Optional[str] #api_ip
    p: Optional[int] #api_port
    api: Optional[bool] #api running

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

def store_miner_metadata(self):
    def get_metadata():
        return MinerMetadata(
            sb=start_block,
            lb=last_block,
            bl=balance_model_last_block,
            n=get_network_id(self.config.network),
            cv=insights.__version__
        )

    try:
        start_block, last_block = self.graph_search.get_min_max_block_height_cache()
        balance_model_last_block = self.balance_search.get_latest_block_number()
        subtensor = self.subtensor
        bt.logging.info(f"Storing miner metadata")
        metadata = get_metadata()
        subtensor.commit(self.wallet, self.config.netuid, Metadata.to_compact(metadata))
        bt.logging.success(f"Stored miner metadata: {metadata}")
        
    except bt.errors.MetadataError as e:
        bt.logging.warning(f"Skipping storing miner metadata, error: {e}")
    except Exception as e:
        bt.logging.warning(f"Skipping storing miner metadata, error: {e}")

def store_validator_metadata(self):
    def get_commitment(netuid: int, uid: int, block: Optional[int] = None) -> str:
        metadata = serving.get_metadata(subtensor, netuid, hotkey, block)
        if metadata is None:
            return None
        commitment = metadata["info"]["fields"][0]
        hex_data = commitment[list(commitment.keys())[0]][2:]
        return bytes.fromhex(hex_data).decode()
    
    try:
        subtensor = bt.subtensor(config=self.config)
        bt.logging.info(f"Storing validator metadata")
        metadata =  ValidatorMetadata(
            ip=self.metagraph.axons[self.uid].ip,
            p=int(self.config.api_port),
            api=self.config.enable_api,
            cv=insights.__version__,
        )

        hotkey= self.wallet.hotkey.ss58_address
        subtensor.get_commitment = get_commitment

        existing_commitment = subtensor.get_commitment(self.config.netuid, self.uid)
        if existing_commitment is not None:
            dual_miner = MinerMetadata.from_compact(existing_commitment)
            if dual_miner.sb is not None:
                bt.logging.info(f"Skipping storing validator metadata, as this is a dual hotkey for miner and validator: {metadata}")
                return

        subtensor.commit(self.wallet, self.config.netuid, metadata.to_compact())
        bt.logging.success(f"Stored validator metadata: {metadata}")
    except bt.errors.MetadataError as e:
        bt.logging.warning(f"Skipping storing validator metadata, error: {e}")
    except Exception as e:
        bt.logging.warning(f"Skipping storing validator metadata, error: {e}")

def get_miners_metadata(config, metagraph):
    def get_commitment(netuid: int, uid: int, block: Optional[int] = None) -> str:
        metadata = serving.get_metadata(subtensor, netuid, hotkey, block)
        if metadata is None:
            return None
        commitment = metadata["info"]["fields"][0]
        hex_data = commitment[list(commitment.keys())[0]][2:]
        return bytes.fromhex(hex_data).decode()

    subtensor = bt.subtensor(config=config)
    subtensor.get_commitment = get_commitment
    miners_metadata = {}
    
    bt.logging.info(f"Getting miners metadata")
    for axon in metagraph.axons:
        if axon.is_serving:
            hotkey = axon.hotkey
            try:
                metadata_str = subtensor.get_commitment(config.netuid, 0)
                if metadata_str is None:
                    continue
                metadata = MinerMetadata.from_compact(metadata_str)
                miners_metadata[hotkey] = metadata
            except:
                bt.logging.warning(f"Error while getting miner metadata for {hotkey}, Skipping...")
                continue

    return miners_metadata