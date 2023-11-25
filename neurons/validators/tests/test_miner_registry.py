import unittest
from random import randint

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from neurons.validators.miner_registry import Base, MinerRegistryManager

connection_string = "sqlite:///test_miner_registry.db"

class TestMinerRegistry(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self):
        # Drop all tables after each test
        Base.metadata.drop_all(self.engine)

    def test_get_miner_proportion(self):
        registry = MinerRegistryManager(db_path=connection_string)

        # Add miners
        registry.store_miner_metadata("key1", "192.168.1.1", "network1",  "model1", 1, 1)
        registry.store_miner_metadata("key2", "192.168.1.2",  "network1",  "model2", 1, 1)
        registry.store_miner_metadata("key3","192.168.1.3",  "network2", "model1", 1, 1)

        # Test proportion calculation
        proportion = registry.get_miner_proportion("network1", "model1")
        self.assertEqual(proportion, 1/3)  # As there's one miner out of three matching the criteria

    def helper_calculate_cheat_factor(self, repetitions, unique_heights):
        registry = MinerRegistryManager(db_path=connection_string)

        hot_key = "400400"
        network = "dogecoin"
        model_type = "test_model_4"

        registry.clear_block_heights(hot_key, network, model_type)  # Clear previous test data

        # Generate test data
        for _ in range(unique_heights):
            random_block_height = randint(75000, 80000)
            registry.store_miner_block_height(hot_key=hot_key, network=network, model_type=model_type, block_height=random_block_height)

        repetitive_height = 76000  # A constant height for repetitions
        for _ in range(repetitions):
            registry.store_miner_block_height(hot_key=hot_key, network=network, model_type=model_type, block_height=repetitive_height)

        # Calculate cheat factor
        factor = registry.calculate_cheat_factor(hot_key=hot_key, network=network, model_type=model_type)
        print(f"Test with {repetitions} repetitions: Cheat factor = {factor}")

    def test_calculate_cheat_factor_all_unique(self):
        self.helper_calculate_cheat_factor(0, 256)

    def test_calculate_cheat_factor_some_repetitions(self):
        self.helper_calculate_cheat_factor(128, 128)

    def test_calculate_cheat_factor_half_repetitions(self):
        self.helper_calculate_cheat_factor(64, 196)

    def test_calculate_cheat_factor_all_repetitions(self):
        self.helper_calculate_cheat_factor(32, 228)

if __name__ == '__main__':
    unittest.main()
