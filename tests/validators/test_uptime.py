import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta
from time import sleep

from neurons.validators.uptime import DowntimeLog, Base, MinerUptimeManager, MinerUptime


# Assuming the Miner and DowntimeLog classes have been imported from the module where they are defined.

class TestMinerUptimeManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database for testing.
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        cls.session_factory = sessionmaker(bind=engine)
        cls.Session = scoped_session(cls.session_factory)

    def setUp(self):
        # Create a new session for each test
        self.session = self.Session()
        self.uptime_manager = MinerUptimeManager('sqlite:///:memory:')  # Re-init to bind to the in-memory DB
        self.uptime_manager.Session = self.Session  # Override the session factory with the test session

    def tearDown(self):
        # Rollback and close session after each test
        self.session.rollback()
        self.session.close()
        self.Session.remove()

    def test_get_miner(self):
        # Setup test data
        miner = MinerUptime(uid='123', hotkey='key123')
        self.session.add(miner)
        self.session.commit()

        # Test get_miner
        result = self.uptime_manager.get_miner('123', 'key123')
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, '123')
        self.assertEqual(result.hotkey, 'key123')

    def test_try_update_miner(self):
        # Initial insert
        self.uptime_manager.try_update_miner('123', 'key123')
        miner = self.session.query(MinerUptime).first()
        self.assertIsNotNone(miner)
        self.assertEqual(miner.uid, '123')
        self.assertEqual(miner.hotkey, 'key123')

        # Update to deregister
        self.uptime_manager.try_update_miner('123', 'key124')
        miner = self.session.query(MinerUptime).filter(MinerUptime.uid == '123').first()
        self.assertTrue(miner.is_deregistered)

    def test_up(self):
        self.uptime_manager.try_update_miner('123', 'key123')
        self.uptime_manager.up('123', 'key123')
        miner = self.uptime_manager.get_miner('123', 'key123')
        self.assertIsNotNone(miner)
        self.assertTrue(len(miner.downtimes) == 0)

    def test_down(self):
        self.uptime_manager.try_update_miner('123', 'key123')
        self.uptime_manager.down('123', 'key123')
        miner = self.uptime_manager.get_miner('123', 'key123')
        self.assertTrue(len(miner.downtimes) == 1)

    def test_up_and_down(self):
        self.uptime_manager.try_update_miner('123', 'key123')
        self.uptime_manager.up('123', 'key123')
        self.uptime_manager.down('123', 'key123')
        self.uptime_manager.up('123', 'key123')
        self.uptime_manager.down('123', 'key123')
        self.uptime_manager.up('123', 'key123')

        miner = self.uptime_manager.get_miner('123', 'key123')
        self.assertIsNotNone(miner)
        self.assertTrue(len(miner.downtimes) == 2)

    def test_calculate_uptime(self):
        self.uptime_manager.try_update_miner('123', 'key123')
        sleep(10)

        self.uptime_manager.down('123', 'key123')
        miner = self.uptime_manager.get_miner('123', 'key123')
        sleep(10)
        self.uptime_manager.up('123', 'key123')

        uptime = self.uptime_manager.calculate_uptime('123', 'key123')
        print(uptime)

if __name__ == '__main__':
    unittest.main()
