import time
import typing
import bittensor as bt
from collections import deque
from insights import protocol
from neurons.miners.blacklist_registry import BlacklistRegistryManager
from neurons.remote_config import MinerConfig

request_timestamps = {}

class BlacklistDiscovery:
    def __init__(self, miner_config: MinerConfig, registry_manager: BlacklistRegistryManager):
        self.blacklist_registry_manager = registry_manager
        self.miner_config = miner_config

    def blacklist_discovery(self, metagraph, synapse: protocol.MinerDiscovery) -> typing.Tuple[bool, str]:
        hotkey = synapse.dendrite.hotkey

        if hotkey in self.miner_config.blacklisted_hotkeys:
            self.blacklist_registry_manager.try_add_to_blacklist(synapse.dendrite.ip, hotkey)
            bt.logging.debug(f"Blacklisted hotkey: {hotkey}")
            return True, "Blacklisted hotkey"

        uid = None
        for _uid, _axon in enumerate(metagraph.axons):
            if _axon.hotkey == hotkey:
                uid = _uid
                break

        if uid is None:
            self.blacklist_registry_manager.try_add_to_blacklist(synapse.dendrite.ip, hotkey)
            bt.logging.debug(f"Hotkey not found in metagraph: {hotkey}")
            return True, "Hotkey not found in metagraph"

        stake = metagraph.neurons[uid].stake.tao
        bt.logging.debug(f"Stake of {hotkey}: {stake}")

        if stake < self.miner_config.stake_threshold:
            bt.logging.debug("Denied due to low stake")
            return True, f"Denied due to low stake: {stake}"

        # Rate Limiting Check
        current_time = time.time()
        if hotkey not in request_timestamps:
            request_timestamps[hotkey] = deque()

        while request_timestamps[hotkey] and current_time - request_timestamps[hotkey][0] > self.miner_config.min_request_period:
            request_timestamps[hotkey].popleft()

        if len(request_timestamps[hotkey]) >= self.miner_config.max_requests:
            bt.logging.debug(f"Request rate exceeded for {hotkey}")
            return True, f"Request rate exceeded for {hotkey}"

        request_timestamps[hotkey].append(current_time)

        if hotkey in self.miner_config.whitelisted_hotkeys:
            return False, "Whitelisted hotkey"

        return True, "Not whitelisted"
