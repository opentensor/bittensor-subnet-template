import os
import time
import json
import requests
import bittensor as bt
import threading

# Constants for configuration URLs
MINER_CONFIG_URL = 'https://subnet-15-cfg.s3.fr-par.scw.cloud/miner.json'
VALIDATOR_CONFIG_URL = 'https://subnet-15-cfg.s3.fr-par.scw.cloud/validator.json'
UPDATE_INTERVAL = 3600  # Time interval for updating configuration in seconds

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
            except Exception as e:
                bt.logging.error(f"Failed to update config from {self.config_url}: {e}")

    def get_config_value(self, key, default=None):
        if self.config_cache:
            value = self.config_cache
            for k in key.split('.'):
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
        self.whitelisted_keys = None
        self.blacklisted_keys = None
        self.max_requests = None
        self.min_request_period = None
        self.stake_threshold = None
        self.config_url = MINER_CONFIG_URL

    def load_and_get_config_values(self):
        # Load remote configuration
        self.load_remote_config()

        # Retrieve specific configuration values
        self.stake_threshold = self.get_config_value('stake_threshold', 0.0)
        self.min_request_period = self.get_config_value('min_request_period', 0.0)
        self.max_requests = self.get_config_value('max_requests', 0.0)
        self.blacklisted_keys = self.get_config_value('blacklisted_keys', [])
        self.whitelisted_keys = self.get_config_value('whitelisted_keys', [])

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
        self.config_url = VALIDATOR_CONFIG_URL

    def load_and_get_config_values(self):
        # Load remote configuration
        self.load_remote_config()

        # Retrieve specific configuration values
        self.process_time_weight = self.get_config_value('process_time_weight', 0.2)
        self.block_height_diff_weight = self.get_config_value('block_height_diff_weight', 0.2)
        self.block_height_recency_weight = self.get_config_value('block_height_recency_weight', 0.2)
        self.blockchain_importance_weight = self.get_config_value('blockchain_importance_weight', 0.2)
        self.cheat_factor_weight = self.get_config_value('cheat_factor_weight', 0.2)
        self.discovery_timeout = self.get_config_value('discovery_timeout', 100)

    def get_network_importance(self, network):
        return self.get_config_value(f'network_importance.{network}', 0.5)

    def get_network_importance_keys(self):
        return self.get_config_value('network_importance', {}).keys()

    def get_cheat_factor(self, network):
        return self.get_config_value(f'cheat_factor.{network}', 128)

    def get_cheat_factor_sample_size(self, network):
        return self.get_config_value(f'cheat_factor_sample_size.{network}', 128)