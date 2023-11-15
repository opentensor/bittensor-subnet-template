import unittest
import datetime
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

    def test_store_miner_metadata(self):
        session = self.Session()
        registry = MinerRegistryManager(db_path=connection_string)

        # Add a new miner
        registry.store_miner_metadata("key1", "192.168.1.1", "network1", "model1")
        # Verify addition
        miner = session.query(MinerRegistry).filter_by(hot_key="key1").first()
        self.assertIsNotNone(miner)
        self.assertEqual(miner.hot_key, "key1")

        # Test updating existing miner
        registry.store_miner_metadata("key1", "192.168.1.2", "network2", "model2")
        # Verify update
        updated_miner = session.query(MinerRegistry).filter_by(hot_key="key1").first()
        self.assertEqual(updated_miner.ip_address, "192.168.1.1")
        session.close()

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

if __name__ == '__main__':
    unittest.main()
