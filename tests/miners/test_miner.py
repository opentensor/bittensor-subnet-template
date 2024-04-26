import unittest
from unittest.mock import patch, MagicMock
from neurons.miners.miner import Miner
from neurons.miners.miner import wait_for_blocks_sync
from insights.protocol import MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING
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
        self.assertEqual(config.netuid, 15)

    def test_get_config_custom_model_types(self):
        # Test with custom arguments
        config = Miner.get_config()

        self.assertEqual(config.network, "bitcoin")
        self.assertEqual(config.netuid, 15)

        
if __name__ == '__main__':
    unittest.main()