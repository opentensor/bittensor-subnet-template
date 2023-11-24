import unittest
from random import randint

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from neurons.validators.miner_registry import MinerRegistry, Base, MinerRegistryManager

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
        session = self.Session()
        registry = MinerRegistryManager(db_path=connection_string)

        # Add miners
        registry.store_miner_metadata("key1", "192.168.1.1", "network1",  "model1")
        registry.store_miner_metadata("key2", "192.168.1.2",  "network1",  "model2")
        registry.store_miner_metadata("key3","192.168.1.3",  "network2", "model1")

        # Test proportion calculation
        proportion = registry.get_miner_proportion("network1", "model1")
        self.assertEqual(proportion, 1/3)  # As there's one miner out of three matching the criteria

        session.close()

    def test_store_miner_metadata(self):
        registry = MinerRegistryManager(db_path=connection_string)

        hot_key = "100100"
        network = "bitcoin"
        model_type = "test_model"

        for _ in range(1024):
            random_block_height = randint(75000, 80000)
            registry.store_miner_block_height(hot_key=hot_key, network=network, model_type=model_type, block_height=random_block_height)
            print(f"Stored block height: {random_block_height}")

        factor = registry.calculate_cheat_factor(hot_key=hot_key, network=network, model_type=model_type)
        print(f"Cheating factor: {factor}")

if __name__ == '__main__':
    unittest.main()
