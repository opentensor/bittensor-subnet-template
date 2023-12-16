import os
import time
import json
import typing
import requests
import bittensor as bt
from collections import deque
from insights import protocol
from neurons.miners.blacklist_registry import BlacklistRegistryManager

last_update_time = 0
update_interval = 3600

def load_blacklist_config(file_name):
    global last_update_time
    current_time = time.time()

    if current_time - last_update_time >= update_interval:
        try:
            url = 'https://ip-blocker.s3.fr-par.scw.cloud/blacklist_discovery.json'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            dir_path = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, 'w') as file:
                json.dump(data, file)

            last_update_time = current_time
        except Exception as e:
            bt.logging.error(f"Failed to update blacklist config: {e}")

    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, file_name)

    with open(file_path, 'r') as file:
        data = json.load(file)
        whitelist = set(data.get('whitelisted_hotkeys', []))
        blacklist = set(data.get('blacklisted_hotkeys', []))
        stake_threshold = data.get('stake_threshold', 20000)
        max_requests = data.get('max_requests', 32)
        min_request_period = data.get('min_request_period', 60)
        return whitelist, blacklist, stake_threshold, max_requests, min_request_period

WHITELISTED_KEYS, BLACKLISTED_KEYS, STAKE_THRESHOLD, MAX_REQUESTS, MIN_REQUEST_PERIOD = load_blacklist_config('blacklist_discovery.json')

request_timestamps = {}

def blacklist_discovery(metagraph, synapse: protocol.MinerDiscovery) -> typing.Tuple[bool, str]:
    hotkey = synapse.dendrite.hotkey

    if hotkey in BLACKLISTED_KEYS:
        BlacklistRegistryManager().try_add_to_blacklist(synapse.dendrite.ip, hotkey)
        return True, "Blacklisted hotkey"

    if hotkey in WHITELISTED_KEYS:
        return False, "Whitelisted hotkey"


    uid = None
    for _uid, _axon in enumerate(metagraph.axons):
        if _axon.hotkey == hotkey:
            uid = _uid
            break

    if uid is None:
        BlacklistRegistryManager().try_add_to_blacklist(synapse.dendrite.ip, hotkey)
        return True, "Hotkey not found in metagraph"

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
