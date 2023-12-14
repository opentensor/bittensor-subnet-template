import unittest
from unittest.mock import MagicMock, patch
import time
from collections import deque
from neurons.miners.blacklists import blacklist_discovery

class TestBlacklistDiscovery(unittest.TestCase):
    def setUp(self):
        self.metagraph = MagicMock()
        self.synapse = MagicMock()
        self.synapse.dendrite = MagicMock()

    @patch('neurons.miners.blacklists.BLACKLISTED_KEYS', new={'bkey1', 'bkey2'})
    @patch('neurons.miners.blacklists.WHITELISTED_KEYS', new={'key1', 'key2'})
    @patch('neurons.miners.blacklists.STAKE_THRESHOLD', new=10)
    @patch('neurons.miners.blacklists.MAX_REQUESTS', new=3)
    @patch('neurons.miners.blacklists.MIN_REQUEST_PERIOD', new=60)
    @patch('neurons.miners.blacklists.request_timestamps', new_callable=lambda: {})
    def test_blacklisted_hotkey(self, mock_request_timestamps):
        self.synapse.dendrite.hotkey = 'bkey1'
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (True, "Blacklisted hotkey"))

    @patch('neurons.miners.blacklists.WHITELISTED_KEYS', new={'key1', 'key2'})
    def test_whitelisted_hotkey(self):
        self.synapse.dendrite.hotkey = 'key1'
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (False, "Whitelisted hotkey"))

    @patch('neurons.miners.blacklists.STAKE_THRESHOLD', new=10)
    def test_low_stake_hotkey(self):
        hotkey = 'low_stake_key'
        uid = 0
        self.synapse.dendrite.hotkey = hotkey

        # Mocking the neuron with low stake
        neuron_mock = MagicMock()
        stake_mock = MagicMock()
        stake_mock.tao = 5  # Setting the 'tao' attribute of the stake mock
        neuron_mock.stake = stake_mock  # Assigning the stake mock to the neuron

        self.metagraph.neurons = {uid: neuron_mock}
        self.metagraph.axons = [MagicMock(hotkey=hotkey)]

        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (True, "Blacklisted due to low stake: 5"))

    @patch('neurons.miners.blacklists.MAX_REQUESTS', new=3)
    @patch('neurons.miners.blacklists.MIN_REQUEST_PERIOD', new=60)
    @patch('neurons.miners.blacklists.request_timestamps', new_callable=lambda: {})
    def test_rate_limiting_exceeded(self, mock_request_timestamps):
        hotkey = 'frequent_key'
        self.synapse.dendrite.hotkey = hotkey

        neuron_mock = MagicMock()
        neuron_mock.stake = MagicMock(return_value=15)
        stake_mock = MagicMock()
        stake_mock.tao = 265
        neuron_mock.stake = stake_mock

        self.metagraph.neurons = { 0 : neuron_mock}
        self.metagraph.axons = [MagicMock(hotkey=hotkey)]
        current_time = time.time()
        mock_request_timestamps[hotkey] = deque([current_time - 30, current_time - 20, current_time - 10], maxlen=3)
        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (True, "Request rate exceeded for frequent_key"))


    @patch('neurons.miners.blacklists.request_timestamps', new_callable=lambda: {})
    def test_acceptable_request(self, mock_request_timestamps):
        hotkey = 'key'
        uid = 0
        self.synapse.dendrite.hotkey = hotkey

        neuron_mock = MagicMock()
        stake_mock = MagicMock()
        stake_mock.tao = 3444445
        neuron_mock.stake = stake_mock

        self.metagraph.neurons = {uid: neuron_mock}
        self.metagraph.axons = [MagicMock(hotkey=hotkey)]

        result = blacklist_discovery(self.metagraph, self.synapse)
        self.assertEqual(result, (False, "All ok"))

if __name__ == '__main__':
    unittest.main()
