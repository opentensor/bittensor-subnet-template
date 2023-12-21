import json
import unittest
from unittest.mock import MagicMock, patch
import time
from neurons.miners.blacklist_registry import BlacklistRegistryManager
from neurons.remote_config import MinerConfig
from insights import protocol
from neurons.miners.blacklists import BlacklistDiscovery
class TestBlacklistDiscovery(unittest.TestCase):
    def setUp(self):
        self.registry_manager = MagicMock(spec=BlacklistRegistryManager)
        self.miner_config = MinerConfig()
        self.blacklist_discovery = BlacklistDiscovery(self.miner_config, self.registry_manager)

        self.metagraph = MagicMock()
        self.synapse = MagicMock(spec=protocol.MinerDiscovery)
        self.synapse.dendrite = MagicMock()
        self.synapse.dendrite.ip = "127.0.0.1"

    def test_blacklisted_hotkey(self):
        self.synapse.dendrite.hotkey = self.miner_config.blacklisted_hotkeys[0]
        result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
        self.assertTrue(result[0])
        self.assertEqual(result[1], "Blacklisted hotkey")

    def test_whitelisted_hotkey(self):
        self.synapse.dendrite.hotkey = self.test_data['whitelisted_hotkeys'][0]
        result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
        self.assertFalse(result[0])
        self.assertEqual(result[1], "Whitelisted hotkey")

    def test_hotkey_not_found_in_metagraph(self):
        self.synapse.dendrite.hotkey = self.test_data['hotkey_not_found_in_metagraph']
        self.metagraph.axons = []
        result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
        self.assertTrue(result[0])
        self.assertEqual(result[1], "Hotkey not found in metagraph")

    def test_hotkey_has_stake_below_threshold(self):
        self.synapse.dendrite.hotkey = self.test_data['hotkey_has_stake_below_threshold']
        self.metagraph.axons = [MagicMock()]
        self.metagraph.neurons = [MagicMock()]
        self.metagraph.neurons[0].stake.tao = self.test_data['stake_threshold'] - 1
        result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
        self.assertTrue(result[0])
        self.assertEqual(result[1], f"Blacklisted due to low stake: {self.test_data['stake_threshold'] - 1}")


    @patch('time.time')
    def test_rate_limiting(self, mock_time):
        self.synapse.dendrite.hotkey = self.test_data['rate_limiting']
        self.metagraph.axons = [MagicMock()]
        self.metagraph.neurons = [MagicMock()]
        self.metagraph.neurons[0].stake.tao = self.test_data['stake_threshold'] + 1

        # Initial time setup
        current_time = 1000.0
        mock_time.return_value = current_time

        # Test rate limiting
        for _ in range(self.test_data['max_requests']):
            result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
            self.assertFalse(result[0])
            self.assertEqual(result[1], "All ok")

        # One more request to trigger rate limiting
        result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
        self.assertTrue(result[0])
        self.assertEqual(result[1], f"Request rate exceeded for {self.test_data['rate_limiting']}")

        # Simulate waiting for min_request_period
        mock_time.return_value += self.test_data['min_request_period'] + 1
        result = self.blacklist_discovery.blacklist_discovery(self.metagraph, self.synapse)
        self.assertFalse(result[0])
        self.assertEqual(result[1], "All ok")


if __name__ == '__main__':
    unittest.main()
