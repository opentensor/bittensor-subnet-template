import json
import threading
import time
import typing
import bittensor as bt
from collections import deque
from insights import protocol
from neurons import VERSION
from neurons.miners.blacklist_registry import BlacklistRegistryManager
from neurons.remote_config import MinerConfig
from neurons.storage import get_validator_metadata

request_timestamps = {}

class BlacklistDiscovery:
    def __init__(self, metagraph, subtensor, config, miner_config: MinerConfig, registry_manager: BlacklistRegistryManager):
        self.subtensor = subtensor
        self.config = config
        self.metagraph = metagraph
        self.blacklist_registry_manager = registry_manager
        self.miner_config = miner_config
        self.validator_metadata = {}

    def set_validator_metadata(self):
        self.validator_metadata = get_validator_metadata(self.config, self.subtensor, self.metagraph)

    def run_validator_metadata_updater(self):
        def updater():
            time.sleep(300)
            while True:
                try:
                    self.validator_metadata = get_validator_metadata(self.config, self.subtensor, self.metagraph)
                    bt.logging.info(f"Updated validator metadata")
                except Exception as e:
                    bt.logging.error(f"Error while updating validator metadata {e}")
                    time.sleep(10)
                time.sleep(300)

        thread = threading.Thread(target=updater)
        thread.daemon = True
        thread.start()

    def blacklist_discovery(self, metagraph, synapse: protocol.MinerDiscovery) -> typing.Tuple[bool, str]:
        hotkey = synapse.dendrite.hotkey

        if self.validator_metadata is None:
            bt.logging.error(f"Validator metadata is None")
            return True, f"Blacklisted hotkey: {hotkey}, because of no metadata"

        # Score 2.0+ validator need to have equal version with miner
        if self.validator_metadata[hotkey]:
            if self.validator_metadata[hotkey].v != VERSION:
                return True, f"Blacklisted hotkey: {hotkey}, because of old version"
        else:
            # Score 1.0 validator will be blacklisted
            return True, f"Blacklisted hotkey: {hotkey}, because of no metadata"

        if hotkey in self.miner_config.blacklisted_hotkeys:
            self.blacklist_registry_manager.try_add_to_blacklist(synapse.dendrite.ip, hotkey)
            return True, f"Blacklisted hotkey: {hotkey}"

        uid = None
        for _uid, _axon in enumerate(metagraph.axons):
            if _axon.hotkey == hotkey:
                uid = _uid
                break

        if uid is None:
            self.blacklist_registry_manager.try_add_to_blacklist(synapse.dendrite.ip, hotkey)
            return True, f"Hotkey not found in metagraph: {hotkey}"

        stake = metagraph.neurons[uid].stake.tao
        bt.logging.debug(f"Stake of {hotkey}: {stake}")

        if stake < self.miner_config.stake_threshold:
            return True, f"Denied due to low stake: {stake}"

        # Rate Limiting Check
        current_time = time.time()
        if hotkey not in request_timestamps:
            request_timestamps[hotkey] = deque()

        while request_timestamps[hotkey] and current_time - request_timestamps[hotkey][0] > self.miner_config.min_request_period:
            request_timestamps[hotkey].popleft()

        if len(request_timestamps[hotkey]) >= self.miner_config.max_requests:
            return True, f"Request rate exceeded for {hotkey}"

        request_timestamps[hotkey].append(current_time)

        if hotkey in self.miner_config.whitelisted_hotkeys:
            return False, "Whitelisted hotkey"

        return True, "Not whitelisted"
