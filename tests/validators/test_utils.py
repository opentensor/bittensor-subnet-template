import unittest
from unittest.mock import Mock
from neurons.validators.utils import get_miner_distributions, count_run_id_per_hotkey, count_hotkeys_per_ip

class TestUtils(unittest.TestCase):
    def test_get_miner_distributions(self):
        # Mock data
        miners_metadata = {
            'hotkey1': Mock(n=1),
            'hotkey2': Mock(n=2),
            'hotkey3': Mock(n=1),
        }
        network_importance_keys = [1, 2]

        # Mock get_network_by_id function
        def mock_get_network_by_id(network_id):
            return network_id

        with unittest.mock.patch('neurons.validators.utils.get_network_by_id', mock_get_network_by_id):
            result = get_miner_distributions(miners_metadata, network_importance_keys)

        # Check the result
        expected_result = {1: 2, 2: 1}
        self.assertEqual(result, expected_result)

    def test_count_run_id_per_hotkey(self):
        # Mock data
        metadata = {
            'hotkey1': Mock(ri=1),
            'hotkey2': Mock(ri=2),
            'hotkey3': Mock(ri=1),
        }

        result = count_run_id_per_hotkey(metadata)

        # Check the result
        expected_result = {'hotkey1': 1, 'hotkey2': 1, 'hotkey3': 1}
        self.assertEqual(result, expected_result)

    def test_count_hotkeys_per_ip(self):
        # Mock data
        class MockAxon:
            def __init__(self, ip):
                self.ip = ip

        axons = [
            MockAxon(ip='192.168.1.1'),
            MockAxon(ip='192.168.1.2'),
            MockAxon(ip='192.168.1.1'),
            MockAxon(ip='192.168.1.3'),
        ]

        result = count_hotkeys_per_ip(axons)

        # Check the result
        expected_result = {'192.168.1.1': 2, '192.168.1.2': 1, '192.168.1.3': 1}
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
