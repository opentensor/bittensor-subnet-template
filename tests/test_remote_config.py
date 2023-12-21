import unittest
import os
from neurons.remote_config import MinerConfig, ValidatorConfig

class TestConfigurations(unittest.TestCase):

    def test_miner_config_load_and_values(self):
        # Create an instance of MinerConfig
        miner_config = MinerConfig()
        miner_config.load_and_get_config_values()

        # Check if the configuration values are as expected
        self.assertIsNotNone(miner_config.stake_threshold)
        self.assertIsInstance(miner_config.stake_threshold, int)
        self.assertIsNotNone(miner_config.min_request_period)
        self.assertIsInstance(miner_config.min_request_period, int)
        self.assertIsNotNone(miner_config.max_requests)
        self.assertIsInstance(miner_config.max_requests, int)
        self.assertIsNotNone(miner_config.blacklisted_keys)
        self.assertIsInstance(miner_config.blacklisted_keys, list)
        self.assertIsNotNone(miner_config.whitelisted_keys)
        self.assertIsInstance(miner_config.whitelisted_keys, list)

    def test_validator_config_load_and_values(self):
        # Create an instance of ValidatorConfig
        validator_config = ValidatorConfig()
        validator_config.load_and_get_config_values()

        # Check if the configuration values are as expected
        self.assertIsNotNone(validator_config.process_time_weight)
        self.assertIsInstance(validator_config.process_time_weight, float)
        self.assertIsNotNone(validator_config.block_height_diff_weight)
        self.assertIsInstance(validator_config.block_height_diff_weight, float)
        self.assertIsNotNone(validator_config.block_height_recency_weight)
        self.assertIsInstance(validator_config.block_height_recency_weight, float)
        self.assertIsNotNone(validator_config.blockchain_importance_weight)
        self.assertIsInstance(validator_config.blockchain_importance_weight, float)
        self.assertIsNotNone(validator_config.cheat_factor_weight)
        self.assertIsInstance(validator_config.cheat_factor_weight, float)

        self.assertIsNotNone(validator_config.get_cheat_factor_sample_size('bitcoin'))
        self.assertIsInstance(validator_config.get_cheat_factor_sample_size('bitcoin'), int)

    def tearDown(self):
        # Clean up any files created or modified during the tests
        if os.path.exists("miner.json"):
            pass #os.remove("miner.json")
        if os.path.exists("validator.json"):
            pass #os.remove("validator.json")

if __name__ == '__main__':
    unittest.main()
