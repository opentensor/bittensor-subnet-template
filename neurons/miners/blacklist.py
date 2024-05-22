import bittensor as bt

from insights import protocol
from neurons.miners.query import is_query_only

import typing
import time

from collections import deque
from neurons import logger

def query_blacklist(self, synapse: protocol.Query) -> typing.Tuple[bool, str]:
        """
        Determine the blacklisting or whitelisting status of a hotkey for protocol.Query.

        Parameters:
        - synapse (protocol.Query).
        
        Returns:
        Tuple[bool, str]: 
        - First element (bool): True if the hotkey is blacklisted, False if whitelisted.
        - Second element (str): Message providing information about the hotkey status.

        Blacklisting Conditions:
        - Base blacklist check
        - Blockchain mismatch
        - Model type mismatch
        - Illegal cypher keywords
        """
        hotkey = synapse.dendrite.hotkey
        # Check if the dendrite hotkey is not voting the sn or not.

        is_blacklist, message = base_blacklist(self, synapse=synapse)
        if is_blacklist:
            return is_blacklist, message
        
        if  self.config.network != synapse.network:
            logger.trace("Blacklisting hot key because of wrong blockchain", miner_hotkey = hotkey)
            return True, "Network not supported."

        if not is_query_only(self.miner_config.query_restricted_keywords, synapse.query):
            logger.trace("Blacklisting hot key because of illegal cypher keywords", miner_hotkey = hotkey)
            return True, "Illegal cypher keywords."
        return False, "Hotkey recognized!"
    
def discovery_blacklist(self, synapse: protocol.Discovery) -> typing.Tuple[bool, str]:
    """
    Perform discovery-specific blacklist checks for a hotkey.

    Parameters:
    - synapse (protocol.Discovery)
    
    Returns:
    Tuple[bool, str]: 
    - First element (bool): True if the hotkey is blacklisted, False if whitelisted.
    - Second element (str): Message providing information about the hotkey status.

    Blacklisting Conditions:
    - Base Blacklist Check
    - Unregistered Hotkey
    - Low TAO Stake
    - Request Rate Limiting
    """
    hotkey = synapse.dendrite.hotkey
    is_blacklist, message = base_blacklist(self, synapse=synapse)
    if is_blacklist:
        return is_blacklist, message
    
    axon_uid = None
    for uid, _axon in enumerate(self.metagraph.axons):  # noqa: B007
        if _axon.hotkey == hotkey:
            axon_uid=uid
            break
    
    if axon_uid is None:
        return True, f"Blacklisted a non registered hotkey's request from {hotkey}"
    
    stake = self.metagraph.neurons[uid].stake.tao
    logger.debug("Stake of hotkey", miner_hotkey = hotkey, stake = stake)

    if stake < self.miner_config.stake_threshold and self.config.mode == 'prod':
        return True, f"Denied due to low stake: {stake}<{self.miner_config.stake_threshold}"

    # Rate Limiting Check
    time_window = self.miner_config.min_request_period
    current_time = time.time()

    if hotkey not in self.request_timestamps:
        self.request_timestamps[hotkey] = deque()

    # Remove timestamps outside the current time window
    while self.request_timestamps[hotkey] and current_time - self.request_timestamps[hotkey][0] > time_window:
        self.request_timestamps[hotkey].popleft()

    # Check if the number of requests exceeds the limit
    if len(self.request_timestamps[hotkey]) >= self.miner_config.max_requests:
        return True, f"Request rate exceeded for {hotkey}"

    self.request_timestamps[hotkey].append(current_time)
    return False, "Hotkey recognized!"
                
def base_blacklist(self, synapse: bt.Synapse) -> typing.Tuple[bool, str]:
    """
    Perform base blacklist checks for a hotkey.

    Parameters:
    - synapse (bt.Synapse)
    
    Returns:
    Tuple[bool, str]: 
    - First element (bool): True if the hotkey is blacklisted, False if recognized.
    - Second element (str): Message providing information about the hotkey status.

    Blacklisting Conditions:
    - Unrecognized Hotkey
    - Blacklisted Hotkey
    - Not Whitelisted

    """

    hotkey = synapse.dendrite.hotkey
    if hotkey not in self.metagraph.hotkeys:
        logger.trace(f"Blacklisting unrecognized hotkey", miner_hotkey = hotkey)
        return True, "Unrecognized hotkey"
    if not self.miner_config.is_grace_period and synapse.version != protocol.VERSION:
        return True, f"Blacklisted: Protocol Version differs miner_version={protocol.VERSION} validator_version={synapse.version} for hotkey: {hotkey}"
    if hotkey in self.miner_config.blacklisted_hotkeys:
        return True, f"Blacklisted hotkey: {hotkey}"
    if hotkey not in self.miner_config.whitelisted_hotkeys and self.config.mode == 'prod':
        return True, f"Not Whitelisted hotkey: {hotkey}"
    return False, "Hotkey recognized"