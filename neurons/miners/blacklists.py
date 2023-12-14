import os
import time
import json
import typing
import bittensor as bt
from collections import deque
from insights import protocol

def load_blacklist_config(file_name):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, file_name)

    with open(file_path, 'r') as file:
        data = json.load(file)
        whitelist = set(data.get('whitelisted_hotkeys', []))
        blacklist = set(data.get('blacklisted_hotkeys', []))
        stake_threshold = data.get('stake_threshold', 10)
        max_requests = data.get('max_requests', 10)
        min_request_period = data.get('min_request_period', 60)
        return whitelist, blacklist, stake_threshold, max_requests, min_request_period

WHITELISTED_KEYS, BLACKLISTED_KEYS, STAKE_THRESHOLD, MAX_REQUESTS, MIN_REQUEST_PERIOD = load_blacklist_config('blacklist_discovery.json')

request_timestamps = {}   # Dictionary to hold request timestamps

def blacklist_discovery(metagraph, synapse: protocol.MinerDiscovery) -> typing.Tuple[bool, str]:
    hotkey = synapse.dendrite.hotkey

    if hotkey in BLACKLISTED_KEYS:
        return True, "Blacklisted hotkey"

    if hotkey in WHITELISTED_KEYS:
        return False, "Whitelisted hotkey"


    uid = None
    for _uid, _axon in enumerate(metagraph.axons):
        if _axon.hotkey == hotkey:
            uid = _uid
            break

    stake = metagraph.neurons[uid].stake.tao
    bt.logging.debug(f"Stake of {hotkey}: {stake}")

    if stake < STAKE_THRESHOLD:
        return True, f"Blacklisted due to low stake: {stake}"

    # Rate Limiting Check
    current_time = time.time()
    if hotkey not in request_timestamps:
        request_timestamps[hotkey] = deque()

    while request_timestamps[hotkey] and current_time - request_timestamps[hotkey][0] > MIN_REQUEST_PERIOD:
        request_timestamps[hotkey].popleft()

    if len(request_timestamps[hotkey]) >= MAX_REQUESTS:
        return True, f"Request rate exceeded for {hotkey}"

    request_timestamps[hotkey].append(current_time)

    return False, "All ok"
