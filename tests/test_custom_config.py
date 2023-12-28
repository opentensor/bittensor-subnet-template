import unittest
from unittest.mock import patch, mock_open
from neurons.miners.custom_miner_config import CustomMinerConfig  # Adjust the import according to your project structure
import json

class TestCustomMinerConfig(unittest.TestCase):

    def test_read_valid_json(self):
        """ Test reading from a valid JSON file """
        valid_json_content = '{"blacklisted_hotkeys": ["key1", "key2", "key3"]}'
        with patch("builtins.open", new_callable=mock_open, read_data=valid_json_content):
            config_reader = CustomMinerConfig()
            self.assertEqual(config_reader.blacklisted_hotkeys, ["key1", "key2", "key3"])

    def test_read_invalid_json(self):
        """ Test reading from an invalid JSON file """
        invalid_json_content = '{"blacklisted_hotkeys": ["key1", "key2", "key3"'
        with patch("builtins.open", new_callable=mock_open, read_data=invalid_json_content):
            with self.assertRaises(json.JSONDecodeError):
                _ = CustomMinerConfig()

    def test_read_nonexistent_file(self):
        """ Test reading from a non-existent file """
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                _ = CustomMinerConfig()

# This allows the test to be run from the command line
if __name__ == '__main__':
    unittest.main()

