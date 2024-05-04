import os
import time
import json
import requests
import bittensor as bt
import numpy as np
import threading

import insights

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

    def dump_values(self):
        attributes = {attr: getattr(self, attr) for attr in dir(self) if not attr.startswith('__') and not callable(getattr(self, attr))}
        return attributes

    def _update_config_periodically(self):
        time.sleep(UPDATE_INTERVAL)
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
                    bt.logging.success(f"Updated config from {self.config_url}")
                    break  # Break the loop if successful
                except requests.exceptions.RequestException as e:
                    retries += 1
                    bt.logging.error(f"Attempt {retries} failed to update config from {self.config_url}: {e}")
                    if retries < MAX_RETRIES:
                        time.sleep(RETRY_INTERVAL)
                except Exception as e:
                    bt.logging.error(f"Non-retryable error occurred: {e}")
                    break

    def get_config_composite_value(self, key, default=None):
        if not self.config_cache or key not in self.config_cache:
            return default
        return self.config_cache[key]

    def get_config_value(self, key, default=None):
        if not self.config_cache or key not in self.config_cache:
            return default
        return self.config_cache[key]

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
        self.blockchain_sync_delta = None
        self.is_grace_period = None
        self.set_weights = True
        self.set_weights_frequency = 6011
        self.store_metadata_frequency = 6000
        self.query_restricted_keywords = None
        self.inmemory_hotkeys = []    
 
    def load_and_get_config_values(self):
        # Load remote configuration
        self.load_remote_config()

        # Retrieve specific configuration values
        self.stake_threshold = self.get_config_value('stake_threshold', 5000)
        self.min_request_period = self.get_config_value('min_request_period', 60)
        self.max_requests = self.get_config_value('max_requests', 128)
        self.blacklisted_hotkeys = self.get_config_value('blacklisted_hotkeys', ["5GcBK8PDrVifV1xAf4Qkkk6KsbsmhDdX9atvk8vyKU8xdU63", "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp", "5Fq5v71D4LX8Db1xsmRSy6udQThcZ8sFDqxQFwnUZ1BuqY5A", "5CVS9d1NcQyWKUyadLevwGxg6LgBcF9Lik6NSnbe5q59jwhE", "5HeKSHGdsRCwVgyrHchijnZJnq4wiv6GqoDLNah8R5WMfnLB", "5FFM6Nvvm78GqyMratgXXvjbqZPi7SHgSQ81nyS96jBuUWgt", "5ED6jwDECEmNvSp98R2qyEUPHDv9pi14E6n3TS8CicD6YfhL"])
        self.whitelisted_hotkeys = self.get_config_value('whitelisted_hotkeys', ["5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", "5HK5tp6t2S59DywmHRWPBVJeJ86T61KjurYqeooqj8sREpeN", "5EhvL1FVkQPpMjZX4MAADcW42i3xPSF1KiCpuaxTYVr28sux", "5CXRfP2ekFhe62r7q3vppRajJmGhTi7vwvb2yr79jveZ282w", "5DvTpiniW9s3APmHRYn8FroUWyfnLtrsid5Mtn5EwMXHN2ed", "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3", "5Hddm3iBFD2GLT5ik7LZnT3XJUnRnN8PoeCFgGQgawUVKNm8", "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2", "5FcXnzNo3mrqReTEY4ftkg5iXRBi61iyvM4W1bywZLRqfxAY", "5HNQURvmjjYhTSksi8Wfsw676b4owGwfLR2BFAQzG7H3HhYf", "5FLKnbMjHY8LarHZvk2q2RY9drWFbpxjAcR5x8tjr3GqtU6F", "5Gpt8XWFTXmKrRF1qaxcBQLvnPLpKi6Pt2XC4vVQR7gqNKtU"])
        self.blockchain_sync_delta = self.get_config_value('blockchain_sync_delta', {'bitcoin': 100})

        self.is_grace_period = self.get_config_value('is_grace_period', False)
        
        # Set_weights, send metadata
        self.set_weights = self.get_config_value('set_weights', True)
        self.set_weights_frequency = self.get_config_value('set_weights_frequency', 6011)
        self.store_metadata_frequency = self.get_config_value('store_metadata_frequency', 6000)
        self.query_restricted_keywords = self.get_config_value('benchmark_restricted_keywords', ['CREATE', 'SET', 'DELETE', 'DETACH', 'REMOVE', 'MERGE', 'CREATE INDEX', 'DROP INDEX', 'CREATE CONSTRAINT', 'DROP CONSTRAINT'])
        
        self.inmemory_hotkeys = self.get_config_value('inmemory_hotkeys', [])
        
        return self
    
    def get_blockchain_sync_delta(self, network):
        self.get_config_composite_value('blockchain_sync_delta', {'bitcoin': 100})


class ValidatorConfig(RemoteConfig):
    def __init__(self):
        super().__init__()
        self.process_time_weight = None
        self.block_height_weight = None
        self.block_height_recency_weight = None
        self.blockchain_importance_weight = None
        
        self.discovery_timeout = None
        self.challenge_timeout = None

        self.blockchain_importance = None
        self.blockchain_recency_weight = None
 
        self.uptime_weight = None
        self.is_grace_period = None

        self.benchmark_enabled = True
        self.benchmark_consensus = 0.51
        self.benchmark_timeout = 600
        self.benchmark_cluster_size = 32
        self.benchmark_query_chunk_size = 5
        self.benchmark_query_diff = 10000

        self.version = None
        self.version_update = True

        self.config_url = os.getenv("VALIDATOR_REMOTE_CONFIG_URL", 'https://subnet-15-cfg.s3.fr-par.scw.cloud/validator3.json')

    def load_and_get_config_values(self):
        self.load_remote_config()

        # Retrieve specific configuration values
        self.process_time_weight = self.get_config_value('process_time_weight', 16)
        self.block_height_weight = self.get_config_value('block_height_weight', 54)
        self.uptime_weight = self.get_config_value('uptime_weight', 16)

        self.block_height_recency_weight = self.get_config_value('block_height_recency_weight',  5)
        self.blockchain_importance_weight = self.get_config_value('blockchain_importance_weight', 1)
        
        self.discovery_timeout = self.get_config_value('discovery_timeout', 6)
        self.challenge_timeout = self.get_config_value('challenge_timeout', 6)

        self.blockchain_importance = self.get_config_value('blockchain_importance', {"bitcoin": 1})
        self.blockchain_recency_weight = self.get_config_value('blockchain_recency_weight',  {"bitcoin": 2})
        self.is_grace_period = self.get_config_value('is_grace_period', False)

        self.benchmark_enabled = self.get_config_value('benchmark_enabled', True)
        self.benchmark_consensus = self.get_config_value('benchmark_consensus', 0.51)

        self.benchmark_timeout = self.get_config_value('benchmark_timeout', 600)
        self.benchmark_cluster_size = self.get_config_value('benchmark_cluster_size', 1)
        self.benchmark_query_chunk_size = self.get_config_value('benchmark_query_chunk_size', 5)
        self.benchmark_query_diff = self.get_config_value('benchmark_query_diff', 10000)

        self.version_update = self.get_config_value('version_update', True)
        self.version = self.get_config_value('version', insights.__version__)

        self.blockchain_importance = self.get_config_value('blockchain_importance', {"bitcoin": 0.9, "doge": 0.1})
        self.blockchain_recency_weight = self.get_config_value('blockchain_recency_weight',  {"bitcoin": 2, "doge": 2})
        self.is_grace_period = self.get_config_value('is_grace_period', False)

        return self

    def get_blockchain_min_blocks(self, network):
        return self.get_config_composite_value(f'blockchain_min_blocks.{network}', 51840)

    def get_network_importance(self, network):
        return self.get_config_composite_value(f'network_importance.{network}', 1)

    def get_networks(self):
        return self.get_config_value('networks', ['bitcoin'])

    def get_blockchain_recency_weight(self, network):
        return self.get_config_composite_value(f'blockchain_recency_weight.{network}', 2)

    def get_benchmark_query_script(self, network):
        return self.get_config_composite_value(f'benchmark_query_script.{network}', """
            import random
            def build_query(network, start_block, end_block, diff = 10000):
                mid_point = start_block + (end_block - start_block) // 2
                block_num = random.randint(mid_point, end_block - diff)
                return f"UNWIND range({block_num}, {block_num + diff}) AS block_height MATCH (p:Transaction) WHERE p.block_height = block_height RETURN SUM(p.block_height);"
            query = build_query(network, start_block, end_block)
            """)
