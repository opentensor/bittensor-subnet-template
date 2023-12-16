import unittest
from neurons.miners.blacklist_registry import BlacklistRegistryManager


class TestBlacklistRegistry(unittest.TestCase):
    def setUp(self):
        # Set up the test environment
        self.manager = BlacklistRegistryManager("sqlite:///:memory:")
        self.manager.remove_all()

    def test_add_and_retrieve_blacklist(self):
        # Test adding to the blacklist
        test_ip = "192.168.1.1"
        test_key = "testkey"

        self.manager.try_add_to_blacklist(test_ip, test_key)

        # Retrieve the blacklist and verify the entry
        blacklist = self.manager.get_blacklist()
        self.assertEqual(len(blacklist), 1)
        self.assertEqual(blacklist[0].ip_address, test_ip)
        self.assertEqual(blacklist[0].hot_key, test_key)

    def test_prevent_duplicate_entries(self):
        # Add the same entry twice
        test_ip = "192.168.1.1"
        test_key = "testkey"

        self.manager.try_add_to_blacklist(test_ip, test_key)
        self.manager.try_add_to_blacklist(test_ip, test_key)

        # Retrieve the blacklist and verify only one entry
        blacklist = self.manager.get_blacklist()
        self.assertEqual(len(blacklist), 1)
        self.assertEqual(blacklist[0].ip_address, test_ip)
        self.assertEqual(blacklist[0].hot_key, test_key)

    def tearDown(self):
        # Clean up after tests
        # self.manager.engine.execute("DELETE FROM blacklist_registry")
        pass


if __name__ == '__main__':
    unittest.main()
