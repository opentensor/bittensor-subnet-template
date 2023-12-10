import unittest
from unittest.mock import MagicMock, patch
import time
from collections import deque
from neurons.miners.blacklist_discovery import blacklist_discovery

class TestBlacklistDiscovery(unittest.TestCase):
    def setUp(self):
        self.metagraph = MagicMock()
        self.synapse = MagicMock()
        self.synapse.dendrite = MagicMock()

    @patch('neurons.miners.blacklist_discovery.BLACKLISTED_KEYS', new={'bkey1', 'bkey2'})
    @patch('neurons.miners.blacklist_discovery.WHITELISTED_KEYS', new={'key1', 'key2'})
    @patch('neurons.miners.blacklist_discovery.STAKE_THRESHOLD', new=10)
    @patch('neurons.miners.blacklist_discovery.MAX_REQUESTS', new=3)
    @patch('neurons.miners.blacklist_discovery.MIN_REQUEST_PERIOD', new=60)
    @patch('neurons.miners.blacklist_discovery.request_timestamps', new_callable=lambda: {})
    def test_blacklisted_hotkey(self, mock_request_timestamps):
        self.synapse.dendrite.hotkey = 'bkey1'
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (True, "Blacklisted hotkey"))

    @patch('neurons.miners.blacklist_discovery.WHITELISTED_KEYS', new={'key1', 'key2'})
    def test_whitelisted_hotkey(self):
        self.synapse.dendrite.hotkey = 'key1'
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (False, "Whitelisted hotkey"))

    @patch('neurons.miners.blacklist_discovery.STAKE_THRESHOLD', new=10)
    def test_low_stake_hotkey(self):
        self.synapse.dendrite.hotkey = 'low_stake_key'
        self.metagraph.neurons = {'low_stake_key': MagicMock(stake=5)}
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (True, "Blacklisted due to low stake: 5"))

    @patch('neurons.miners.blacklist_discovery.MAX_REQUESTS', new=3)
    @patch('neurons.miners.blacklist_discovery.MIN_REQUEST_PERIOD', new=60)
    @patch('neurons.miners.blacklist_discovery.request_timestamps', new_callable=lambda: {})
    def test_rate_limiting_exceeded(self, mock_request_timestamps):
        hotkey = 'frequent_key'
        self.synapse.dendrite.hotkey = hotkey

        # Mocking the stake to be above the threshold
        self.metagraph.neurons = {hotkey: MagicMock(stake=15)}

        current_time = time.time()
        mock_request_timestamps[hotkey] = deque([current_time - 30, current_time - 20, current_time - 10], maxlen=3)
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (True, "Request rate exceeded for frequent_key"))


    @patch('neurons.miners.blacklist_discovery.request_timestamps', new_callable=lambda: {})
    def test_acceptable_request(self, mock_request_timestamps):
        self.synapse.dendrite.hotkey = 'normal_key'
        self.metagraph.neurons = {'normal_key': MagicMock(stake=15)}
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (False, "All ok"))

if __name__ == '__main__':
    unittest.main()
