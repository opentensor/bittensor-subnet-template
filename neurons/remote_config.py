import os
import time
import json
import requests
import bittensor as bt
import threading

# Constants for configuration URLs

UPDATE_INTERVAL = 3600  # Time interval for updating configuration in seconds
MAX_RETRIES = 10
RETRY_INTERVAL = 5

class RemoteConfig:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(RemoteConfig, cls).__new__(cls)
        return cls._instances[cls]

    def __init__(self):
        self.config_cache = None
        self.last_update_time = 0
        self.config_url = None
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._update_config_periodically)
        self.thread.daemon = True
        self.thread.start()

    def _update_config_periodically(self):
        while not self.stop_event.is_set():
            self.load_remote_config()
            time.sleep(UPDATE_INTERVAL)

    def load_remote_config(self):
        if self.config_url is None:
            return

        current_time = time.time()
        if current_time - self.last_update_time >= UPDATE_INTERVAL or self.config_cache is None:
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    response = requests.get(self.config_url, timeout=10)
                    response.raise_for_status()
                    self.config_cache = response.json()

                    file_name = os.path.basename(self.config_url)
                    dir_path = os.path.dirname(os.path.abspath(__file__))
                    file_path = os.path.join(dir_path, file_name)
                    with open(file_path, 'w') as file:
                        json.dump(self.config_cache, file)

                    self.last_update_time = current_time
                    bt.logging.info(f"Updated config from {self.config_url}")
                    break  # Break the loop if successful
                except requests.exceptions.RequestException as e:
                    retries += 1
                    bt.logging.error(f"Attempt {retries} failed to update config from {self.config_url}: {e}")
                    if retries < MAX_RETRIES:
                        time.sleep(RETRY_INTERVAL)
                except Exception as e:
                    bt.logging.error(f"Non-retryable error occurred: {e}")
                    break

    def get_config_value(self, key, default=None):
        if self.config_cache:
            keys = key.split('.') if '.' in key else [key]
            value = self.config_cache
            for k in keys:
                if k in value:
                    value = value[k]
                else:
                    return default
            return value
        return default

    def stop_update_thread(self):
        self.stop_event.set()
        self.thread.join()

class MinerConfig(RemoteConfig):
    def __init__(self):
        super().__init__()
        self.whitelisted_hotkeys = None
        self.blacklisted_hotkeys = None
        self.max_requests = None
        self.min_request_period = None
        self.stake_threshold = None
        self.config_url = os.getenv("MINER_REMOTE_CONFIG_URL", 'https://subnet-15-cfg.s3.fr-par.scw.cloud/miner.json')

    def load_and_get_config_values(self):
        # Load remote configuration
        self.load_remote_config()

        # Retrieve specific configuration values
        self.stake_threshold = self.get_config_value('stake_threshold', 20000)
        self.min_request_period = self.get_config_value('min_request_period', 60)
        self.max_requests = self.get_config_value('max_requests', 128)
        self.blacklisted_hotkeys = self.get_config_value('blacklisted_hotkeys', ["5GcBK8PDrVifV1xAf4Qkkk6KsbsmhDdX9atvk8vyKU8xdU63", "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp", "5Fq5v71D4LX8Db1xsmRSy6udQThcZ8sFDqxQFwnUZ1BuqY5A", "5CVS9d1NcQyWKUyadLevwGxg6LgBcF9Lik6NSnbe5q59jwhE", "5HeKSHGdsRCwVgyrHchijnZJnq4wiv6GqoDLNah8R5WMfnLB", "5FFM6Nvvm78GqyMratgXXvjbqZPi7SHgSQ81nyS96jBuUWgt", "5ED6jwDECEmNvSp98R2qyEUPHDv9pi14E6n3TS8CicD6YfhL"])
        self.whitelisted_hotkeys = self.get_config_value('whitelisted_hotkeys', ["5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", "5HK5tp6t2S59DywmHRWPBVJeJ86T61KjurYqeooqj8sREpeN", "5EhvL1FVkQPpMjZX4MAADcW42i3xPSF1KiCpuaxTYVr28sux", "5CXRfP2ekFhe62r7q3vppRajJmGhTi7vwvb2yr79jveZ282w", "5DvTpiniW9s3APmHRYn8FroUWyfnLtrsid5Mtn5EwMXHN2ed", "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3", "5Hddm3iBFD2GLT5ik7LZnT3XJUnRnN8PoeCFgGQgawUVKNm8", "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2", "5FcXnzNo3mrqReTEY4ftkg5iXRBi61iyvM4W1bywZLRqfxAY", "5HNQURvmjjYhTSksi8Wfsw676b4owGwfLR2BFAQzG7H3HhYf", "5FLKnbMjHY8LarHZvk2q2RY9drWFbpxjAcR5x8tjr3GqtU6F", "5Gpt8XWFTXmKrRF1qaxcBQLvnPLpKi6Pt2XC4vVQR7gqNKtU"])

class ValidatorConfig(RemoteConfig):
    def __init__(self):
        super().__init__()
        self.cheat_factor_weight = None
        self.blockchain_importance_weight = None
        self.block_height_recency_weight = None
        self.block_height_diff_weight = None
        self.process_time_weight = None
        self.cheat_factor_sample_size = None
        self.discovery_timeout = None
        self.config_url = os.getenv("VALIDATOR_REMOTE_CONFIG_URL", 'https://subnet-15-cfg.s3.fr-par.scw.cloud/validator.json')

    def load_and_get_config_values(self):
        # Load remote configuration
        self.load_remote_config()

        # Retrieve specific configuration values
        self.process_time_weight = self.get_config_value('process_time_weight', 0.5)
        self.block_height_diff_weight = self.get_config_value('block_height_diff_weight', 1.5)
        self.block_height_recency_weight = self.get_config_value('block_height_recency_weight',  1.5)
        self.blockchain_importance_weight = self.get_config_value('blockchain_importance_weight', 0.2)
        self.cheat_factor_weight = self.get_config_value('cheat_factor_weight', 3)
        self.discovery_timeout = self.get_config_value('discovery_timeout', 100)

    def get_network_importance(self, network):
        return self.get_config_value(f'network_importance.{network}', 0.5)

    def get_network_importance_keys(self):
        return self.get_config_value('network_importance', {}).keys()

    def get_cheat_factor(self, network):
        return self.get_config_value(f'cheat_factor.{network}', 128)

    def get_cheat_factor_sample_size(self, network):
        return self.get_config_value(f'cheat_factor_sample_size.{network}', 128)

    def get_block_height_recency_scale_factor(self, network):
        return self.get_config_value(f'block_height_recency_scale_factor.{network}', 100)