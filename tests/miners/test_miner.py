import unittest
from unittest.mock import patch, MagicMock
from neurons.miners.miner import Miner
from neurons.miners.miner import wait_for_blocks_sync
import sys
import os

class TestMiner(unittest.TestCase):

    def setUp(self):
        self.original_argv = sys.argv.copy()
        self.original_environ = os.environ.copy()

    def tearDown(self):
        sys.argv = self.original_argv
        os.environ.update(self.original_environ)

    def test_get_config_defaults(self):
        # Test with default arguments
        config = Miner.get_config()

        self.assertEqual(config.network, "bitcoin")
        self.assertEqual(config.model_type, "funds_flow")
        self.assertEqual(config.netuid, 15)
        self.assertEqual(config.mode, "prod")

    def test_get_config_staging(self):
        # Test with custom arguments
        custom_args = [
            "--mode", "staging"
        ]
        sys.argv = sys.argv + custom_args
        config = Miner.get_config()

        self.assertEqual(config.network, "bitcoin")
        self.assertEqual(config.model_type, "funds_flow")
        self.assertEqual(config.netuid, 1)
        self.assertEqual(config.mode, "staging")


    def test_get_config_testnet(self):
            # Test with custom arguments
            custom_args = [
                "--mode", "testnet"
            ]
            sys.argv = sys.argv + custom_args
            config = Miner.get_config()

            self.assertEqual(config.network, "bitcoin")
            self.assertEqual(config.model_type, "funds_flow")
            self.assertEqual(config.netuid, 59)
            self.assertEqual(config.mode, "testnet")
        

        
if __name__ == '__main__':
    unittest.main()